import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePageHeader } from "@/components/layout/PageHeaderContext";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { RepositoryBreadcrumb, WorkspaceTabs } from "@/features/repositories/RepositoryHeader";
import { useRepository } from "@/features/repositories/useRepository";
import { GuidanceForm } from "@/features/guidance/GuidanceForm";
import { StepList } from "@/features/guidance/StepList";
import { getGuidance } from "@/services/guidance";
import type { GuidanceResponse } from "@/types/guidance";

export default function GuidancePage() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();
  const { repository, isLoading, error, refetch } = useRepository(repositoryId);

  const [guidanceResponse, setGuidanceResponse] = useState<GuidanceResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  usePageHeader(
    {
      breadcrumb: repository ? <RepositoryBreadcrumb repository={repository} /> : undefined,
      actions: repository ? (
        <WorkspaceTabs
          active="guidance"
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

  const handleGenerate = async (task: string) => {
    if (!repositoryId) return;
    try {
      setIsGenerating(true);
      setGenerateError(null);
      const res = await getGuidance(repositoryId, task);
      setGuidanceResponse(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to generate developer guidance.";
      setGenerateError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) return <LoadingState message="Loading repository..." />;
  if (error || !repository) return <ErrorState message={error ?? "Repository not found."} onRetry={refetch} />;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-6 lg:p-8">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary">
          Developer Guidance Engine
        </h2>
        <p className="mt-1 text-xs text-text-muted">
          Generate step-by-step implementation blueprints grounded in existing repository modules and patterns.
        </p>
      </div>

      <GuidanceForm onGenerate={handleGenerate} isLoading={isGenerating} />

      {generateError && (
        <div className="rounded-lg border border-error/30 bg-error-muted p-4 text-xs text-error">
          {generateError}
        </div>
      )}

      {guidanceResponse && (
        <StepList task={guidanceResponse.task} steps={guidanceResponse.steps} />
      )}
    </div>
  );
}
