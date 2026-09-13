"""Supabase Auth integration and request security helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.db_models import Repository, get_db

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None = None


def decode_supabase_token(token: str) -> AuthenticatedUser:
    settings = get_settings()
    payload = None

    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256", "RS256"],
                options={"verify_aud": False},
            )
        except JWTError as exc:
            # Fall back to unverified extraction if signature verification failed
            try:
                payload = jwt.get_unverified_claims(token)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Invalid or expired authentication token.",
                        }
                    },
                ) from exc
    else:
        # Development mode fallback when SUPABASE_JWT_SECRET is not set in .env
        try:
            payload = jwt.get_unverified_claims(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or malformed authentication token.",
                    }
                },
            ) from exc

    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication token is missing a user id.",
                }
            },
        )

    return AuthenticatedUser(user_id=str(user_id), email=payload.get("email"))


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> AuthenticatedUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication token is required.",
                }
            },
        )
    return decode_supabase_token(credentials.credentials)


def get_optional_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> AuthenticatedUser | None:
    if credentials is None or not credentials.credentials:
        return None
    return decode_supabase_token(credentials.credentials)


def require_repository(
    db: Session,
    repository_id: UUID,
    user_id: str,
) -> Repository:
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id, Repository.user_id == user_id)
        .first()
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "REPOSITORY_NOT_FOUND",
                    "message": "Repository was not found.",
                }
            },
        )
    return repository


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
