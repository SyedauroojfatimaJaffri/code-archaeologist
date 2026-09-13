import { CheckCircle2, ShieldAlert, Sparkles, Download, ArrowLeft } from "lucide-react";
import type { OffboardingReportResponse } from "@/types/offboarding";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface ReportViewProps {
  report: OffboardingReportResponse;
  onBack?: () => void;
}

export function ReportView({ report, onBack }: ReportViewProps) {
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-4xl mx-auto">
      {/* Action Header */}
      <div className="flex items-center justify-between">
        {onBack && (
          <Button variant="secondary" size="sm" onClick={onBack}>
            <ArrowLeft className="size-4" />
            <span>Back to Sessions</span>
          </Button>
        )}
        <Button variant="secondary" size="sm" onClick={handlePrint} className="ml-auto">
          <Download className="size-4" />
          <span>Export / Print Report</span>
        </Button>
      </div>

      {/* Main Handover Report Document */}
      <Card className="flex flex-col gap-8 p-8 bg-surface border-border">
        {/* Document Title Header */}
        <div className="flex flex-col gap-2 border-b border-border pb-6">
          <div className="flex items-center gap-2">
            <Badge variant="accent">Preserved Knowledge Transfer</Badge>
            <span className="text-xs text-text-muted">
              Session ID: {report.session_id.slice(0, 8)}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-text-primary">
            Engineering Offboarding Report
          </h2>
          <div className="flex items-center gap-4 text-xs text-text-muted">
            {report.contributor && <span>Departing Contributor: <strong className="text-text-primary">{report.contributor}</strong></span>}
            {report.generated_at && (
              <span>Generated: {new Date(report.generated_at).toLocaleDateString()}</span>
            )}
          </div>
        </div>

        {/* Executive Summary */}
        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-accent">
            1. Executive Knowledge Summary
          </h3>
          <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap bg-surface-elevated p-4 rounded-lg border border-border">
            {report.summary}
          </p>
        </div>

        {/* Key Architectural Decisions */}
        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-accent">
            2. Key Architectural Decisions Preserved
          </h3>
          {report.key_decisions && report.key_decisions.length > 0 ? (
            <div className="flex flex-col gap-2">
              {report.key_decisions.map((decision, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 rounded-lg border border-border bg-surface-elevated p-3.5"
                >
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                  <span className="text-sm text-text-primary">{decision}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted">No explicit architectural decisions recorded.</p>
          )}
        </div>

        {/* Undocumented Areas & Watch-outs */}
        <div className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-accent">
            3. Undocumented Areas & Technical Watch-outs
          </h3>
          {report.undocumented_areas && report.undocumented_areas.length > 0 ? (
            <div className="flex flex-col gap-2">
              {report.undocumented_areas.map((area, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 rounded-lg border border-warning/30 bg-warning-muted/40 p-3.5"
                >
                  <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" />
                  <span className="text-sm text-text-primary">{area}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-muted">No critical undocumented areas reported.</p>
          )}
        </div>

        {/* Preserved Knowledge Items */}
        {report.knowledge_items && report.knowledge_items.length > 0 && (
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-accent">
              4. Extracted Domain Knowledge Items
            </h3>
            <div className="flex flex-col gap-3">
              {report.knowledge_items.map((item, idx) => (
                <div
                  key={idx}
                  className="flex flex-col gap-2 rounded-lg border border-border bg-surface-elevated p-4"
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="size-4 text-accent" />
                    <span className="text-sm font-semibold text-text-primary">
                      {String(item.title ?? `Knowledge Item #${idx + 1}`)}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary leading-relaxed whitespace-pre-wrap">
                    {String(item.content ?? item.answer ?? "")}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
