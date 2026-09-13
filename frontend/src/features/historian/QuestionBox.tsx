import React, { useState } from "react";
import { Search, Sparkles, CornerDownLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QuestionBoxProps {
  onAsk: (question: string) => void;
  isLoading?: boolean;
}

const SAMPLE_QUESTIONS = [
  "Why does the authentication middleware enforce custom JWT checks?",
  "What was the motivation behind adding the database migration script?",
  "Why is the workspace cleanup logic wrapped in a retry handler?",
  "How did the repository structure evolve between major releases?",
];

export function QuestionBox({ onAsk, isLoading }: QuestionBoxProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onAsk(question.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSampleClick = (sample: string) => {
    setQuestion(sample);
    onAsk(sample);
  };

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="relative flex flex-col rounded-xl border border-border bg-surface shadow-lg transition-all focus-within:border-accent">
        <div className="flex items-start gap-3 p-4">
          <Search className="mt-1 size-5 shrink-0 text-text-muted" />
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the Code Historian why this code exists (e.g. 'Why was this pattern used in routes_repositories.py?')..."
            rows={3}
            disabled={isLoading}
            className="w-full resize-none bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between border-t border-border bg-surface-elevated/50 px-4 py-2.5">
          <div className="flex items-center gap-1 text-[11px] text-text-muted">
            <kbd className="rounded border border-border-strong px-1.5 py-0.5 font-mono text-[10px] text-text-secondary">Ctrl</kbd>
            <span>+</span>
            <kbd className="rounded border border-border-strong px-1.5 py-0.5 font-mono text-[10px] text-text-secondary">Enter</kbd>
            <span className="ml-1">to ask</span>
          </div>

          <Button type="submit" isLoading={isLoading} disabled={!question.trim() || isLoading} size="sm">
            <Sparkles className="size-3.5" />
            <span>Investigate</span>
            <CornerDownLeft className="size-3 opacity-60" />
          </Button>
        </div>
      </form>

      {/* Suggested prompts */}
      <div className="flex flex-col gap-2">
        <span className="text-xs font-medium text-text-muted">Archaeological Inquiry Suggestions:</span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_QUESTIONS.map((sample, idx) => (
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
