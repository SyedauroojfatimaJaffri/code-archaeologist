import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePageHeader } from "@/components/layout/PageHeaderContext";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { RepositoryBreadcrumb, WorkspaceTabs } from "@/features/repositories/RepositoryHeader";
import { useRepository } from "@/features/repositories/useRepository";
import { OffboardingWorkspace } from "@/features/offboarding/OffboardingWorkspace";
import {
  createOffboardingSession,
  getOffboardingSession,
  answerOffboardingQuestion,
  getOffboardingReport,
} from "@/services/offboarding";
import type {
  OffboardingSessionDetailResponse,
  OffboardingReportResponse,
} from "@/types/offboarding";

export default function OffboardingPage() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();
  const { repository, isLoading: repoLoading, error: repoError, refetch } = useRepository(repositoryId);

  const [session, setSession] = useState<OffboardingSessionDetailResponse | null>(null);
  const [report, setReport] = useState<OffboardingReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  usePageHeader(
    {
      breadcrumb: repository ? <RepositoryBreadcrumb repository={repository} /> : undefined,
      actions: repository ? (
        <WorkspaceTabs
          active="offboarding"
          onChange={(tab) => {
            if (tab === "overview") navigate(`/repositories/${repository.repository_id}`);
            else if (tab === "code") navigate(`/repositories/${repository.repository_id}/explorer`);
            else navigate(`/repositories/${repository.repository_id}/${tab}`);
          }}
        />
      ) : undefined,
    },
    [repository?.repository_id]
  );

  const handleCreateSession = async (contributor: string) => {
    if (!repositoryId) return;
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await createOffboardingSession(repositoryId, contributor);
      const detail = await getOffboardingSession(repositoryId, res.session_id);
      setSession(detail);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create offboarding session.";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerQuestion = async (questionId: string, answer: string) => {
    if (!repositoryId || !session) return;
    try {
      await answerOffboardingQuestion(repositoryId, session.session_id, questionId, answer);
      const updated = await getOffboardingSession(repositoryId, session.session_id);
      setSession(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit answer.";
      setErrorMsg(msg);
    }
  };

  const handleFetchReport = async () => {
    if (!repositoryId || !session) return;
    try {
      setIsLoading(true);
      const rep = await getOffboardingReport(repositoryId, session.session_id);
      setReport(rep);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate offboarding report.";
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  if (repoLoading) return <LoadingState message="Loading repository..." />;
  if (repoError || !repository) return <ErrorState message={repoError ?? "Repository not found."} onRetry={refetch} />;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6 lg:p-8">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary">
          Developer Offboarding & Knowledge Preservation
        </h2>
        <p className="mt-1 text-xs text-text-muted">
          Conduct AI-guided offboarding interviews to prevent institutional brain drain before key contributors depart.
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-lg border border-error/30 bg-error-muted p-4 text-xs text-error">
          {errorMsg}
        </div>
      )}

      <OffboardingWorkspace
        session={session}
        report={report}
        onCreateSession={handleCreateSession}
        onAnswerQuestion={handleAnswerQuestion}
        onFetchReport={handleFetchReport}
        isLoading={isLoading}
      />
    </div>
  );
}
