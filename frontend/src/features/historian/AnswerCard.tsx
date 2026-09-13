import { Sparkles, HelpCircle, ShieldCheck, FileSearch, Info } from "lucide-react";
import type { HistorianQuestionResponse, ConfidenceLevel, ClassificationType } from "@/types/historian";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EvidencePanel } from "./EvidencePanel";

interface AnswerCardProps {
  question: string;
  response: HistorianQuestionResponse;
}

export function AnswerCard({ question, response }: AnswerCardProps) {
  const getConfidenceBadge = (confidence?: ConfidenceLevel) => {
    switch (confidence) {
      case "high":
        return <Badge variant="success" dot>High Confidence</Badge>;
      case "medium":
        return <Badge variant="warning" dot>Medium Confidence</Badge>;
      case "low":
        return <Badge variant="error" dot>Low Confidence</Badge>;
      default:
        return <Badge variant="neutral">Unrated</Badge>;
    }
  };

  const getClassificationBadge = (classification?: ClassificationType) => {
    switch (classification) {
      case "verified":
        return (
          <Badge variant="success" className="gap-1">
            <ShieldCheck className="size-3" />
            Verified
          </Badge>
        );
      case "inferred":
        return (
          <Badge variant="info" className="gap-1">
            <FileSearch className="size-3" />
            Inferred
          </Badge>
        );
      case "human_knowledge":
        return (
          <Badge variant="accent" className="gap-1">
            <Sparkles className="size-3" />
            Human Knowledge
          </Badge>
        );
      default:
        return <Badge variant="neutral">General</Badge>;
    }
  };

  return (
    <Card className="flex flex-col gap-6 p-6 animate-fade-in border-border bg-surface-elevated">
      {/* Header with question and badges */}
      <div className="flex flex-col gap-3 border-b border-border pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-accent-muted text-accent">
            <HelpCircle className="size-4" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-text-primary">
              {question}
            </h3>
            <p className="mt-0.5 text-xs text-text-muted">
              Archaeological Analysis & History Investigation
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:self-start">
          {getClassificationBadge(response.classification)}
          {getConfidenceBadge(response.confidence)}
        </div>
      </div>

      {/* Answer Body */}
      <div className="flex flex-col gap-4">
        <div className="prose prose-invert max-w-none text-sm leading-relaxed text-text-primary">
          <p className="whitespace-pre-wrap">{response.answer}</p>
        </div>

        {response.gap_detected && (
          <div className="flex items-center gap-2.5 rounded-lg border border-warning/30 bg-warning-muted p-3.5 text-xs text-warning">
            <Info className="size-4 shrink-0" />
            <span>
              Insufficient historical records found for complete certainty. This question has been logged as an open knowledge gap.
            </span>
          </div>
        )}

        {/* Evidence list */}
        <div className="pt-2">
          <EvidencePanel evidence={response.evidence} />
        </div>
      </div>
    </Card>
  );
}
