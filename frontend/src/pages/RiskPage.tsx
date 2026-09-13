import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { usePageHeader } from "@/components/layout/PageHeaderContext";
import { LoadingState } from "@/components/common/LoadingState";
import { ErrorState } from "@/components/common/ErrorState";
import { RepositoryBreadcrumb, WorkspaceTabs } from "@/features/repositories/RepositoryHeader";
import { useRepository } from "@/features/repositories/useRepository";
import { RiskDashboard } from "@/features/risk/RiskDashboard";
import { getRisks } from "@/services/risk";
import type { RiskItem } from "@/types/risk";

export default function RiskPage() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();
  const { repository, isLoading: repoLoading, error: repoError, refetch } = useRepository(repositoryId);

  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [isLoadingRisks, setIsLoadingRisks] = useState(true);
  const [riskError, setRiskError] = useState<string | null>(null);

  usePageHeader(
    {
      breadcrumb: repository ? <RepositoryBreadcrumb repository={repository} /> : undefined,
      actions: repository ? (
        <WorkspaceTabs
          active="risk"
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

  useEffect(() => {
    if (!repositoryId) return;
    setIsLoadingRisks(true);
    setRiskError(null);
    getRisks(repositoryId)
      .then((res) => setRisks(res.risks || []))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Failed to load risk analysis.";
        setRiskError(message);
      })
      .finally(() => setIsLoadingRisks(false));
  }, [repositoryId]);

  if (repoLoading) return <LoadingState message="Loading repository..." />;
  if (repoError || !repository) return <ErrorState message={repoError ?? "Repository not found."} onRetry={refetch} />;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6 lg:p-8">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-text-primary">
          Codebase Risk & Complexity Radar
        </h2>
        <p className="mt-1 text-xs text-text-muted">
          Automated evaluation of structural fragility, churn hotspots, and complex dependencies.
        </p>
      </div>

      {isLoadingRisks ? (
        <LoadingState message="Analyzing codebase risk signals..." />
      ) : riskError ? (
        <ErrorState message={riskError} onRetry={() => refetch()} />
      ) : (
        <RiskDashboard risks={risks} />
      )}
    </div>
  );
}
