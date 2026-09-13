import { useState } from "react";
import { AlertTriangle, ShieldCheck, Flame, FileCode } from "lucide-react";
import type { RiskItem } from "@/types/risk";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface RiskDashboardProps {
  risks: RiskItem[];
}

export function RiskDashboard({ risks }: RiskDashboardProps) {
  const [filter, setFilter] = useState<"all" | "high" | "medium" | "low">("all");

  const highRiskCount = risks.filter((r) => r.score >= 0.7).length;
  const mediumRiskCount = risks.filter((r) => r.score >= 0.4 && r.score < 0.7).length;
  const lowRiskCount = risks.filter((r) => r.score < 0.4).length;

  const filteredRisks = risks.filter((r) => {
    if (filter === "high") return r.score >= 0.7;
    if (filter === "medium") return r.score >= 0.4 && r.score < 0.7;
    if (filter === "low") return r.score < 0.4;
    return true;
  });

  const getScoreBadge = (score: number) => {
    const percentage = Math.round(score * 100);
    if (score >= 0.7) {
      return (
        <Badge variant="error" dot className="gap-1">
          <Flame className="size-3" />
          {percentage}% High Risk
        </Badge>
      );
    }
    if (score >= 0.4) {
      return (
        <Badge variant="warning" dot className="gap-1">
          <AlertTriangle className="size-3" />
          {percentage}% Moderate Risk
        </Badge>
      );
    }
    return (
      <Badge variant="success" dot className="gap-1">
        <ShieldCheck className="size-3" />
        {percentage}% Low Risk
      </Badge>
    );
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Risk Metrics Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="flex flex-col gap-2 p-5 bg-surface border-border">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>High-Risk Hotspots</span>
            <Flame className="size-4 text-error" />
          </div>
          <div className="font-mono text-2xl font-bold text-error">
            {highRiskCount}
          </div>
          <span className="text-[11px] text-text-muted">
            Files requiring architectural scrutiny
          </span>
        </Card>

        <Card className="flex flex-col gap-2 p-5 bg-surface border-border">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>Moderate Risk</span>
            <AlertTriangle className="size-4 text-warning" />
          </div>
          <div className="font-mono text-2xl font-bold text-warning">
            {mediumRiskCount}
          </div>
          <span className="text-[11px] text-text-muted">
            Components with growing complexity
          </span>
        </Card>

        <Card className="flex flex-col gap-2 p-5 bg-surface border-border">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span>Stable / Low Risk</span>
            <ShieldCheck className="size-4 text-success" />
          </div>
          <div className="font-mono text-2xl font-bold text-success">
            {lowRiskCount}
          </div>
          <span className="text-[11px] text-text-muted">
            Well-isolated, low churn components
          </span>
        </Card>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h3 className="text-sm font-semibold text-text-primary">
          Codebase Risk Assessment ({filteredRisks.length})
        </h3>
        <div className="flex items-center gap-1.5">
          {(["all", "high", "medium", "low"] as const).map((tab) => (
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

      {/* Risk Items List */}
      {filteredRisks.length === 0 ? (
        <div className="rounded-lg border border-border bg-surface p-8 text-center text-sm text-text-muted">
          No files match the selected risk filter.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filteredRisks.map((item) => (
            <Card
              key={item.file_id}
              className="flex flex-col gap-3 p-4 transition-colors hover:border-border-strong bg-surface"
            >
              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                <div className="flex items-center gap-2">
                  <FileCode className="size-4 text-text-muted" />
                  <span className="font-mono text-xs font-medium text-text-primary">
                    {item.file_path ?? item.file_id}
                  </span>
                </div>
                {getScoreBadge(item.score)}
              </div>

              {item.explanation && (
                <p className="text-xs text-text-secondary leading-relaxed">
                  {item.explanation}
                </p>
              )}

              {item.signals && Object.keys(item.signals).length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] uppercase tracking-wider text-text-muted mr-1">
                    Signals:
                  </span>
                  {Object.entries(item.signals).map(([key, val]) => (
                    <Badge key={key} variant="neutral" className="text-[10px]">
                      {key.replace(/_/g, " ")}: {String(val)}
                    </Badge>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
