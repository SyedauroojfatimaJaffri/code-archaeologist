import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePageHeader } from "@/components/layout/PageHeaderContext";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { RepositoryBreadcrumb, WorkspaceTabs } from "@/features/repositories/RepositoryHeader";
import { useRepository } from "@/features/repositories/useRepository";
import { QuestionBox } from "@/features/historian/QuestionBox";
import { AnswerCard } from "@/features/historian/AnswerCard";
import { askHistorian } from "@/services/historian";
import type { HistorianQuestionResponse } from "@/types/historian";

export default function HistorianPage() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();
  const { repository, isLoading, error, refetch } = useRepository(repositoryId);

  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const [response, setResponse] = useState<HistorianQuestionResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  usePageHeader(
    {
      breadcrumb: repository ? <RepositoryBreadcrumb repository={repository} /> : undefined,
      actions: repository ? (
        <WorkspaceTabs
          active="historian"
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

  const handleAsk = async (question: string) => {
    if (!repositoryId) return;
    try {
      setIsAsking(true);
      setAskError(null);
      setCurrentQuestion(question);
      const res = await askHistorian(repositoryId, question);
      setResponse(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to analyze question.";
      setAskError(message);
    } finally {
      setIsAsking(false);
    }
  };

  if (isLoading) return <LoadingState message="Loading repository..." />;
  if (error || !repository) return <ErrorState message={error ?? "Repository not found."} onRetry={refetch} />;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-6 lg:p-8">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary">
          Code Historian
        </h2>
        <p className="mt-1 text-xs text-text-muted">
          Ask why specific files, architectures, or decisions exist in <strong className="text-text-secondary">{repository.name ?? repository.github_url}</strong>.
        </p>
      </div>

      <QuestionBox onAsk={handleAsk} isLoading={isAsking} />

      {askError && (
        <div className="rounded-lg border border-error/30 bg-error-muted p-4 text-xs text-error">
          {askError}
        </div>
      )}

      {response && <AnswerCard question={currentQuestion} response={response} />}
    </div>
  );
}
