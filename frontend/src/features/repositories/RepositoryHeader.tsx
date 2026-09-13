import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { StatusBadge } from "@/components/common/StatusBadge";
import { cn } from "@/lib/utils";
import type { AnalysisStatus, Repository } from "@/types/repository";
import { parseOwnerAndName } from "./repository.types";

export function RepositoryBreadcrumb({ repository }: { repository: Repository }) {
  const { owner, name } = repository.owner
    ? { owner: repository.owner, name: repository.name ?? "" }
    : parseOwnerAndName(repository.github_url);

  return (
    <div className="flex min-w-0 items-center gap-1.5 text-sm">
      <Link to="/repositories" className="focus-ring shrink-0 rounded text-text-muted hover:text-text-secondary">
        Code Archaeologist
      </Link>
      <ChevronRight className="size-3.5 shrink-0 text-text-muted" aria-hidden="true" />
      <span className="truncate font-medium text-text-primary">
        {owner}/{name}
      </span>
    </div>
  );
}

export type WorkspaceTab =
  | "overview"
  | "code"
  | "historian"
  | "guidance"
  | "risk"
  | "knowledge"
  | "offboarding"
  | "history"
  | "architecture";

const TABS: { id: WorkspaceTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "code", label: "Code" },
  { id: "historian", label: "Historian" },
  { id: "guidance", label: "Guidance" },
  { id: "risk", label: "Risk" },
  { id: "knowledge", label: "Knowledge Gaps" },
  { id: "offboarding", label: "Offboarding" },
  { id: "history", label: "History" },
  { id: "architecture", label: "Architecture" },
];

export function WorkspaceTabs({
  active,
  onChange,
}: {
  active: WorkspaceTab;
  onChange: (tab: WorkspaceTab) => void;
}) {
  return (
    <nav className="flex items-center gap-1 overflow-x-auto" aria-label="Repository workspace sections">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={cn(
            "focus-ring shrink-0 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
            active === tab.id
              ? "bg-surface-elevated text-text-primary border border-border"
              : "text-text-muted hover:bg-surface-elevated hover:text-text-primary"
          )}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}

export function RepositoryStatusRow({ repository }: { repository: Repository }) {
  const status = (repository.status === "created" ? "not_analyzed" : repository.status) as AnalysisStatus;
  return <StatusBadge status={status} />;
}
