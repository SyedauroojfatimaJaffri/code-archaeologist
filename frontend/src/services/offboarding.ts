import { api } from "./api";
import type {
  OffboardingAnswerRequest,
  OffboardingAnswerResponse,
  OffboardingCreateRequest,
  OffboardingCreateResponse,
  OffboardingReportResponse,
  OffboardingSessionDetailResponse,
} from "@/types/offboarding";

export async function createOffboardingSession(
  repositoryId: string,
  contributor: string
): Promise<OffboardingCreateResponse> {
  const payload: OffboardingCreateRequest = { contributor };
  return api.post<OffboardingCreateResponse>(
    `/repositories/${repositoryId}/offboarding`,
    payload
  );
}

export async function getOffboardingSession(
  repositoryId: string,
  sessionId: string
): Promise<OffboardingSessionDetailResponse> {
  return api.get<OffboardingSessionDetailResponse>(
    `/repositories/${repositoryId}/offboarding/${sessionId}`
  );
}

export async function answerOffboardingQuestion(
  repositoryId: string,
  sessionId: string,
  questionId: string,
  answer: string
): Promise<OffboardingAnswerResponse> {
  const payload: OffboardingAnswerRequest = { question_id: questionId, answer };
  return api.post<OffboardingAnswerResponse>(
    `/repositories/${repositoryId}/offboarding/${sessionId}/answer`,
    payload
  );
}

export async function getOffboardingReport(
  repositoryId: string,
  sessionId: string
): Promise<OffboardingReportResponse> {
  return api.get<OffboardingReportResponse>(
    `/repositories/${repositoryId}/offboarding/${sessionId}/report`
  );
}
