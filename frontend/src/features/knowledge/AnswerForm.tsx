import React, { useState } from "react";
import { BookPlus, CheckCircle2 } from "lucide-react";
import type { KnowledgeGapItem } from "@/types/knowledge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface AnswerFormProps {
  gap: KnowledgeGapItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (gapId: string, answer: string) => Promise<void>;
}

export function AnswerForm({ gap, isOpen, onClose, onSubmit }: AnswerFormProps) {
  const [answer, setAnswer] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gap || !answer.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      await onSubmit(gap.gap_id, answer.trim());
      setAnswer("");
      onClose();
    } catch {
      // Error handled by parent or toast
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!gap) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg bg-surface border-border">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-text-primary">
            <BookPlus className="size-5 text-accent" />
            <span>Provide Human Knowledge</span>
          </DialogTitle>
          <DialogDescription className="text-xs text-text-muted">
            Resolve this knowledge gap by explaining the engineering context. This will be preserved in the Knowledge Store for future developers.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 pt-2">
          {/* Question context display */}
          <div className="rounded-lg border border-border bg-surface-elevated p-3.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Unanswered Question
            </span>
            <p className="mt-1 text-sm font-medium text-text-primary">
              {gap.question}
            </p>
            {gap.context && (
              <p className="mt-1 text-xs text-text-secondary">
                {gap.context}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-text-secondary">
              Your Explanation / Architectural Rationale
            </label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Explain why this decision was made, constraints encountered, or design intentions..."
              rows={5}
              required
              className="w-full rounded-lg border border-border bg-bg p-3 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              disabled={!answer.trim() || isSubmitting}
            >
              <CheckCircle2 className="size-4" />
              <span>Submit Knowledge</span>
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
