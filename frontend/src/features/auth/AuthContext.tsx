import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import type { AuthSession, AuthStatus } from "./auth.types";

interface AuthContextValue {
  status: AuthStatus;
  session: AuthSession | null;
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signUp: (email: string, password: string) => Promise<{ error: string | null; needsConfirmation?: boolean }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function toAuthSession(supabaseSession: {
  access_token: string;
  user: { id: string; email?: string | null };
} | null): AuthSession | null {
  if (!supabaseSession) return null;
  return {
    accessToken: supabaseSession.access_token,
    user: {
      id: supabaseSession.user.id,
      email: supabaseSession.user.email ?? "",
    },
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [session, setSession] = useState<AuthSession | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setStatus("unauthenticated");
      return;
    }

    let mounted = true;

    supabase.auth
      .getSession()
      .then(({ data, error }) => {
        if (!mounted) return;
        if (error) {
          // eslint-disable-next-line no-console
          console.warn("[auth] Failed to retrieve session:", error.message);
        }
        const nextSession = toAuthSession(data?.session ?? null);
        setSession(nextSession);
        setStatus(nextSession ? "authenticated" : "unauthenticated");
      })
      .catch((err) => {
        if (!mounted) return;
        // eslint-disable-next-line no-console
        console.warn("[auth] Session initialization error:", err);
        setStatus("unauthenticated");
      });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      const nextSession = toAuthSession(newSession);
      setSession(nextSession);
      setStatus(nextSession ? "authenticated" : "unauthenticated");
    });

    return () => {
      mounted = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      session,
      signIn: async (email: string, password: string) => {
        if (!isSupabaseConfigured) {
          return {
            error:
              "Authentication is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env.",
          };
        }
        try {
          const trimmedEmail = email.trim();
          const { data, error } = await supabase.auth.signInWithPassword({
            email: trimmedEmail,
            password,
          });
          if (error) {
            return { error: error.message };
          }
          if (data.session) {
            const nextSession = toAuthSession(data.session);
            setSession(nextSession);
            setStatus("authenticated");
          }
          return { error: null };
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : "An unexpected authentication error occurred.";
          return { error: message };
        }
      },
      signUp: async (email: string, password: string) => {
        if (!isSupabaseConfigured) {
          return {
            error:
              "Authentication is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env.",
          };
        }
        try {
          const trimmedEmail = email.trim();
          const { data, error } = await supabase.auth.signUp({
            email: trimmedEmail,
            password,
          });
          if (error) {
            return { error: error.message };
          }
          if (data.session) {
            const nextSession = toAuthSession(data.session);
            setSession(nextSession);
            setStatus("authenticated");
            return { error: null, needsConfirmation: false };
          }
          if (data.user && !data.session) {
            return { error: null, needsConfirmation: true };
          }
          return { error: null };
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : "An unexpected sign-up error occurred.";
          return { error: message };
        }
      },
      signOut: async () => {
        if (!isSupabaseConfigured) return;
        try {
          await supabase.auth.signOut();
        } catch (err) {
          // eslint-disable-next-line no-console
          console.warn("[auth] Error signing out:", err);
        }
      },
    }),
    [status, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
