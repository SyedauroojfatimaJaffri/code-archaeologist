import { FileCode, ChevronRight } from "lucide-react";
import type { GuidanceStep } from "@/types/guidance";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface StepListProps {
  task: string;
  steps: GuidanceStep[];
}

export function StepList({ task, steps }: StepListProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center text-sm text-text-muted">
        No implementation steps generated. Try clarifying or expanding your task description.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      <div className="flex flex-col gap-1 border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <Badge variant="accent">Implementation Blueprint</Badge>
          <span className="text-xs text-text-muted">{steps.length} sequential steps</span>
        </div>
        <h3 className="text-lg font-semibold text-text-primary">
          {task}
        </h3>
      </div>

      <div className="flex flex-col gap-4">
        {steps.map((step, idx) => {
          const stepNumber = step.order ?? idx + 1;
          return (
            <Card
              key={idx}
              className="flex flex-col gap-4 p-5 transition-all hover:border-border-strong bg-surface"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-accent/15 font-mono text-xs font-bold text-accent">
                    {stepNumber}
                  </div>
                  <h4 className="text-sm font-semibold text-text-primary">
                    {step.title}
                  </h4>
                </div>
                <Badge variant="neutral" className="text-[10px]">
                  Step {stepNumber} of {steps.length}
                </Badge>
              </div>

              {/* Reasoning */}
              <p className="text-xs leading-relaxed text-text-secondary">
                {step.reasoning}
              </p>

              {/* Targeted files */}
              {step.files && step.files.length > 0 && (
                <div className="flex flex-col gap-2 rounded-lg border border-border-strong/40 bg-surface-elevated p-3">
                  <div className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-text-muted">
                    <FileCode className="size-3.5 text-accent" />
                    <span>Relevant Files ({step.files.length})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {step.files.map((file, fileIdx) => (
                      <div
                        key={fileIdx}
                        className="flex items-center gap-1 rounded bg-bg px-2 py-1 font-mono text-xs text-text-primary border border-border"
                      >
                        <ChevronRight className="size-3 text-text-muted" />
                        <span>{file}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
