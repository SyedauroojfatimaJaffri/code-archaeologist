import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePageHeader } from "@/components/layout/PageHeaderContext";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { RepositoryBreadcrumb, WorkspaceTabs } from "@/features/repositories/RepositoryHeader";
import { useRepository } from "@/features/repositories/useRepository";
import { KnowledgeGapList } from "@/features/knowledge/KnowledgeGapList";
import { getKnowledgeGaps, answerKnowledgeGap } from "@/services/knowledge";
import type { KnowledgeGapItem } from "@/types/knowledge";

export default function KnowledgePage() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();
  const { repository, isLoading: repoLoading, error: repoError, refetch } = useRepository(repositoryId);

  const [gaps, setGaps] = useState<KnowledgeGapItem[]>([]);
  const [isLoadingGaps, setIsLoadingGaps] = useState(true);
  const [gapError, setGapError] = useState<string | null>(null);

  usePageHeader(
    {
      breadcrumb: repository ? <RepositoryBreadcrumb repository={repository} /> : undefined,
      actions: repository ? (
        <WorkspaceTabs
          active="knowledge"
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

  const loadGaps = () => {
    if (!repositoryId) return;
    setIsLoadingGaps(true);
    setGapError(null);
    getKnowledgeGaps(repositoryId)
      .then((res) => setGaps(res.gaps || []))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Failed to load knowledge gaps.";
        setGapError(message);
      })
      .finally(() => setIsLoadingGaps(false));
  };

  useEffect(() => {
    loadGaps();
  }, [repositoryId]);

  const handleAnswerGap = async (gapId: string, answer: string) => {
    if (!repositoryId) return;
    await answerKnowledgeGap(repositoryId, gapId, answer);
    loadGaps();
  };

  if (repoLoading) return <LoadingState message="Loading repository..." />;
  if (repoError || !repository) return <ErrorState message={repoError ?? "Repository not found."} onRetry={refetch} />;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6 lg:p-8">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary">
          Knowledge Gaps & Human Preservation
        </h2>
        <p className="mt-1 text-xs text-text-muted">
          Review detected documentation blind spots and contribute domain knowledge to preserve architectural rationale.
        </p>
      </div>

      {isLoadingGaps ? (
        <LoadingState message="Loading knowledge gaps..." />
      ) : gapError ? (
        <ErrorState message={gapError} onRetry={loadGaps} />
      ) : (
        <KnowledgeGapList gaps={gaps} onAnswerGap={handleAnswerGap} />
      )}
    </div>
  );
}
