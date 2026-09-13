import { useState } from "react";
import { HelpCircle, CheckCircle2, MessageSquarePlus } from "lucide-react";
import type { KnowledgeGapItem } from "@/types/knowledge";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AnswerForm } from "./AnswerForm";

interface KnowledgeGapListProps {
  gaps: KnowledgeGapItem[];
  onAnswerGap: (gapId: string, answer: string) => Promise<void>;
}

export function KnowledgeGapList({ gaps, onAnswerGap }: KnowledgeGapListProps) {
  const [selectedGap, setSelectedGap] = useState<KnowledgeGapItem | null>(null);
  const [filter, setFilter] = useState<"all" | "open" | "resolved">("all");

  const openCount = gaps.filter((g) => g.status === "open").length;
  const resolvedCount = gaps.filter((g) => g.status === "resolved").length;

  const filteredGaps = gaps.filter((g) => {
    if (filter === "open") return g.status === "open";
    if (filter === "resolved") return g.status === "resolved";
    return true;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "high":
        return <Badge variant="error">High Priority</Badge>;
      case "medium":
        return <Badge variant="warning">Medium Priority</Badge>;
      default:
        return <Badge variant="neutral">Low Priority</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Knowledge Gap Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="flex flex-col gap-2 p-5 bg-surface border-border">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>Open Knowledge Gaps</span>
            <HelpCircle className="size-4 text-warning" />
          </div>
          <div className="font-mono text-2xl font-bold text-warning">
            {openCount}
          </div>
          <span className="text-[11px] text-text-muted">
            Areas where codebase history lacked conclusive evidence
          </span>
        </Card>

        <Card className="flex flex-col gap-2 p-5 bg-surface border-border">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>Resolved with Human Knowledge</span>
            <CheckCircle2 className="size-4 text-success" />
          </div>
          <div className="font-mono text-2xl font-bold text-success">
            {resolvedCount}
          </div>
          <span className="text-[11px] text-text-muted">
            Context preserved in the permanent Knowledge Store
          </span>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h3 className="text-sm font-semibold text-text-primary">
          Knowledge Gaps ({filteredGaps.length})
        </h3>
        <div className="flex items-center gap-1.5">
          {(["all", "open", "resolved"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                filter === tab
                  ? "bg-surface-elevated text-text-primary border border-border"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Gaps List */}
      {filteredGaps.length === 0 ? (
        <div className="rounded-lg border border-border bg-surface p-8 text-center text-sm text-text-muted">
          No knowledge gaps match the selected filter.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filteredGaps.map((gap) => (
            <Card
              key={gap.gap_id}
              className="flex flex-col gap-4 p-5 transition-colors hover:border-border-strong bg-surface"
            >
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                <div className="flex items-start gap-3">
                  <div
                    className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md ${
                      gap.status === "resolved"
                        ? "bg-success-muted text-success"
                        : "bg-warning-muted text-warning"
                    }`}
                  >
                    {gap.status === "resolved" ? (
                      <CheckCircle2 className="size-4" />
                    ) : (
                      <HelpCircle className="size-4" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">
                      {gap.question}
                    </h4>
                    {gap.context && (
                      <p className="mt-1 text-xs text-text-secondary leading-relaxed">
                        {gap.context}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start">
                  {getPriorityBadge(gap.priority)}
                  {gap.status === "resolved" ? (
                    <Badge variant="success" dot>
                      Resolved
                    </Badge>
                  ) : (
                    <Badge variant="warning" dot>
                      Open
                    </Badge>
                  )}
                </div>
              </div>

              {gap.status === "open" && (
                <div className="flex items-center justify-end border-t border-border pt-3">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setSelectedGap(gap)}
                  >
                    <MessageSquarePlus className="size-3.5" />
                    <span>Provide Answer</span>
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Modal Dialog for answering */}
      <AnswerForm
        gap={selectedGap}
        isOpen={Boolean(selectedGap)}
        onClose={() => setSelectedGap(null)}
        onSubmit={async (gapId, answer) => {
          await onAnswerGap(gapId, answer);
          setSelectedGap(null);
        }}
      />
    </div>
  );
}
