import { useState, type FormEvent } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "./AuthContext";

interface FieldErrors {
  email?: string;
  password?: string;
}

function validate(email: string, password: string, mode: "signIn" | "signUp"): FieldErrors {
  const errors: FieldErrors = {};
  const trimmed = email.trim();
  if (!trimmed) {
    errors.email = "Email is required.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    errors.email = "Enter a valid email address.";
  }
  if (!password) {
    errors.password = "Password is required.";
  } else if (mode === "signUp" && password.length < 6) {
    errors.password = "Password must be at least 6 characters.";
  }
  return errors;
}

export function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<"signIn" | "signUp">("signIn");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setAuthError(null);
    setAuthSuccess(null);

    const fieldErrors = validate(email, password, mode);
    setErrors(fieldErrors);
    if (Object.keys(fieldErrors).length > 0) return;

    setIsSubmitting(true);

    if (mode === "signIn") {
      const result = await signIn(email, password);
      setIsSubmitting(false);

      if (result.error) {
        setAuthError(result.error);
        return;
      }

      onSuccess();
    } else {
      const result = await signUp(email, password);
      setIsSubmitting(false);

      if (result.error) {
        setAuthError(result.error);
        return;
      }

      if (result.needsConfirmation) {
        setAuthSuccess(
          "Registration successful! Please check your email to confirm your account, then sign in."
        );
        setMode("signIn");
      } else {
        onSuccess();
      }
    }
  }

  function handleModeToggle() {
    setAuthError(null);
    setAuthSuccess(null);
    setErrors({});
    setMode((prev) => (prev === "signIn" ? "signUp" : "signIn"));
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      {authError && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-md border border-error/30 bg-error-muted px-3 py-2.5 text-sm text-error"
        >
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <div className="flex flex-col gap-1">
            <span>{authError}</span>
            {authError.toLowerCase().includes("invalid login credentials") && (
              <span className="text-xs opacity-90">
                Don't have an account yet?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setAuthError(null);
                    setMode("signUp");
                  }}
                  className="font-medium underline hover:opacity-100"
                >
                  Create one now
                </button>
              </span>
            )}
          </div>
        </div>
      )}

      {authSuccess && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-md border border-success/30 bg-success-muted px-3 py-2.5 text-sm text-success"
        >
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
          <span>{authSuccess}</span>
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? "email-error" : undefined}
        />
        {errors.email && (
          <p id="email-error" className="text-xs text-error">
            {errors.email}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete={mode === "signIn" ? "current-password" : "new-password"}
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          invalid={Boolean(errors.password)}
          aria-describedby={errors.password ? "password-error" : undefined}
        />
        {errors.password && (
          <p id="password-error" className="text-xs text-error">
            {errors.password}
          </p>
        )}
      </div>

      <Button type="submit" size="lg" className="mt-1 w-full" isLoading={isSubmitting}>
        {mode === "signIn" ? "Sign in" : "Create account"}
      </Button>

      <div className="text-center">
        <button
          type="button"
          onClick={handleModeToggle}
          className="text-xs text-text-muted hover:text-text-primary transition-colors"
        >
          {mode === "signIn"
            ? "Don't have an account? Sign up"
            : "Already have an account? Sign in"}
        </button>
      </div>
    </form>
  );
}
