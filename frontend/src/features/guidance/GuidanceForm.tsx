import React, { useState } from "react";
import { Compass, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface GuidanceFormProps {
  onGenerate: (task: string) => void;
  isLoading?: boolean;
}

const SAMPLE_TASKS = [
  "Add rate limiting to the public API endpoints",
  "Implement a caching layer for repository tree traversal",
  "Introduce support for custom webhook notifications",
  "Refactor user authorization middleware to use JWT claims directly",
];

export function GuidanceForm({ onGenerate, isLoading }: GuidanceFormProps) {
  const [task, setTask] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim() || isLoading) return;
    onGenerate(task.trim());
  };

  const handleSampleClick = (sample: string) => {
    setTask(sample);
    onGenerate(sample);
  };

  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={handleSubmit}
        className="relative flex flex-col rounded-xl border border-border bg-surface shadow-lg transition-all focus-within:border-accent"
      >
        <div className="flex items-start gap-3 p-4">
          <Compass className="mt-1 size-5 shrink-0 text-accent" />
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="Describe the task or feature you want to build (e.g. 'Add a new endpoint for fetching user activity logs')..."
            rows={3}
            disabled={isLoading}
            className="w-full resize-none bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between border-t border-border bg-surface-elevated/50 px-4 py-2.5">
          <span className="text-[11px] text-text-muted">
            The guidance engine maps codebase dependencies to plan exact steps.
          </span>

          <Button
            type="submit"
            isLoading={isLoading}
            disabled={!task.trim() || isLoading}
            size="sm"
          >
            <Sparkles className="size-3.5" />
            <span>Generate Plan</span>
            <ArrowRight className="size-3 opacity-60" />
          </Button>
        </div>
      </form>

      {/* Suggested tasks */}
      <div className="flex flex-col gap-2">
        <span className="text-xs font-medium text-text-muted">Example Engineering Tasks:</span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_TASKS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSampleClick(sample)}
              disabled={isLoading}
              className="focus-ring rounded-lg border border-border bg-surface-elevated px-3 py-1.5 text-left text-xs text-text-secondary transition-colors hover:border-accent/40 hover:bg-surface-hover hover:text-text-primary disabled:opacity-50"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
