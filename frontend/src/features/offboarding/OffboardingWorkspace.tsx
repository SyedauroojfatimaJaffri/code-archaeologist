import React, { useState } from "react";
import { UserMinus, Send, FileText, Sparkles, HelpCircle } from "lucide-react";
import type {
  OffboardingSessionDetailResponse,
  OffboardingReportResponse,
} from "@/types/offboarding";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ReportView } from "./ReportView";

interface OffboardingWorkspaceProps {
  session: OffboardingSessionDetailResponse | null;
  report: OffboardingReportResponse | null;
  onCreateSession: (contributor: string) => Promise<void>;
  onAnswerQuestion: (questionId: string, answer: string) => Promise<void>;
  onFetchReport: () => Promise<void>;
  isLoading?: boolean;
}

export function OffboardingWorkspace({
  session,
  report,
  onCreateSession,
  onAnswerQuestion,
  onFetchReport,
  isLoading,
}: OffboardingWorkspaceProps) {
  const [contributorInput, setContributorInput] = useState("");
  const [activeAnswers, setActiveAnswers] = useState<Record<string, string>>({});
  const [submittingQuestionId, setSubmittingQuestionId] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contributorInput.trim()) return;
    await onCreateSession(contributorInput.trim());
    setContributorInput("");
  };

  const handleAnswerSubmit = async (questionId: string) => {
    const text = activeAnswers[questionId];
    if (!text || !text.trim()) return;
    try {
      setSubmittingQuestionId(questionId);
      await onAnswerQuestion(questionId, text.trim());
      setActiveAnswers((prev) => ({ ...prev, [questionId]: "" }));
    } finally {
      setSubmittingQuestionId(null);
    }
  };

  if (showReport && report) {
    return <ReportView report={report} onBack={() => setShowReport(false)} />;
  }

  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-4xl mx-auto">
      {/* Session Header / Creation */}
      {!session ? (
        <Card className="flex flex-col gap-5 p-6 bg-surface border-border">
          <div className="flex items-start gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent-muted text-accent">
              <UserMinus className="size-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-text-primary">
                Preserve Departing Engineer Knowledge
              </h3>
              <p className="mt-1 text-xs text-text-muted">
                Create an AI-guided knowledge preservation session tailored to a departing contributor's commits, modules, and decisions.
              </p>
            </div>
          </div>

          <form onSubmit={handleCreate} className="flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={contributorInput}
              onChange={(e) => setContributorInput(e.target.value)}
              placeholder="Enter contributor name or GitHub handle (e.g. 'alice', 'octocat')..."
              className="flex-1 rounded-lg border border-border bg-bg px-3.5 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
              required
            />
            <Button type="submit" isLoading={isLoading} disabled={!contributorInput.trim() || isLoading}>
              <Sparkles className="size-4" />
              <span>Start Offboarding Interview</span>
            </Button>
          </form>
        </Card>
      ) : (
        <Card className="flex flex-col gap-4 p-6 bg-surface border-border">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div className="flex items-center gap-3">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-accent-muted text-accent">
                <UserMinus className="size-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-text-primary">
                  Offboarding Interview: {session.contributor ?? "Contributor Session"}
                </h3>
                <span className="text-[11px] text-text-muted">
                  Session ID: {session.session_id.slice(0, 8)} • Status: {session.status}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={async () => {
                  await onFetchReport();
                  setShowReport(true);
                }}
              >
                <FileText className="size-4" />
                <span>View Knowledge Report</span>
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Questions Workspace */}
      {session && session.questions && session.questions.length > 0 && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h4 className="text-sm font-semibold text-text-primary">
              Preservation Questions ({session.questions.length})
            </h4>
            <span className="text-xs text-text-muted">
              {session.questions.filter((q) => q.status === "answered").length} answered
            </span>
          </div>

          <div className="flex flex-col gap-4">
            {session.questions.map((q) => {
              const isAnswered = q.status === "answered" || Boolean(q.answer);
              return (
                <Card
                  key={q.question_id}
                  className="flex flex-col gap-3 p-5 bg-surface border-border transition-colors hover:border-border-strong"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5">
                      <HelpCircle className="mt-0.5 size-4 shrink-0 text-accent" />
                      <h5 className="text-sm font-semibold text-text-primary">
                        {q.question}
                      </h5>
                    </div>
                    {isAnswered ? (
                      <Badge variant="success" dot className="shrink-0">
                        Answered
                      </Badge>
                    ) : (
                      <Badge variant="warning" dot className="shrink-0">
                        Pending
                      </Badge>
                    )}
                  </div>

                  {isAnswered && q.answer ? (
                    <div className="rounded-lg border border-border bg-surface-elevated p-3 text-xs text-text-secondary leading-relaxed">
                      <strong className="text-text-primary block mb-1">Preserved Answer:</strong>
                      {q.answer}
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2.5 pt-2 border-t border-border">
                      <textarea
                        value={activeAnswers[q.question_id] || ""}
                        onChange={(e) =>
                          setActiveAnswers((prev) => ({
                            ...prev,
                            [q.question_id]: e.target.value,
                          }))
                        }
                        placeholder="Provide details on decisions, nuances, undocumented context, or gotchas..."
                        rows={3}
                        className="w-full rounded-lg border border-border bg-bg p-3 text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
                      />
                      <div className="flex justify-end">
                        <Button
                          size="sm"
                          isLoading={submittingQuestionId === q.question_id}
                          disabled={
                            !activeAnswers[q.question_id]?.trim() ||
                            submittingQuestionId === q.question_id
                          }
                          onClick={() => handleAnswerSubmit(q.question_id)}
                        >
                          <Send className="size-3.5" />
                          <span>Submit Context</span>
                        </Button>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
