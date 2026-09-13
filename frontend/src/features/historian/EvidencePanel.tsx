import { GitCommit, FileCode, GitPullRequest, AlertCircle, BookOpen } from "lucide-react";
import type { EvidenceItem } from "@/types/historian";
import { Badge } from "@/components/ui/badge";

interface EvidencePanelProps {
  evidence: EvidenceItem[];
}

export function EvidencePanel({ evidence }: EvidencePanelProps) {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-4 text-xs text-text-muted">
        No specific historical artifacts attached as direct evidence.
      </div>
    );
  }

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType.toLowerCase()) {
      case "commit":
        return <GitCommit className="size-4 text-accent" aria-hidden="true" />;
      case "file":
        return <FileCode className="size-4 text-info" aria-hidden="true" />;
      case "pull_request":
      case "pr":
        return <GitPullRequest className="size-4 text-success" aria-hidden="true" />;
      case "knowledge_item":
        return <BookOpen className="size-4 text-warning" aria-hidden="true" />;
      default:
        return <AlertCircle className="size-4 text-text-muted" aria-hidden="true" />;
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Supporting Evidence ({evidence.length})
        </h4>
      </div>

      <div className="flex flex-col gap-2.5">
        {evidence.map((item, idx) => (
          <div
            key={`${item.source_type}-${item.source_id}-${idx}`}
            className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-3.5 transition-colors hover:border-border-strong"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {getSourceIcon(item.source_type)}
                <span className="font-mono text-xs font-medium text-text-primary">
                  {item.source_id}
                </span>
              </div>
              <Badge variant="neutral" className="text-[10px] uppercase">
                {item.source_type}
              </Badge>
            </div>

            {item.excerpt && (
              <div className="rounded border border-border-strong/50 bg-bg p-2 font-mono text-xs text-text-secondary">
                {item.excerpt}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
