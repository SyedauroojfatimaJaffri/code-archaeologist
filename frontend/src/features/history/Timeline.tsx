import { useState } from "react";
import { GitCommit, GitPullRequest, CircleDot, Calendar, User, Search, Filter } from "lucide-react";
import type { TimelineEvent } from "@/types/history";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface TimelineProps {
  events: TimelineEvent[];
}

export function Timeline({ events }: TimelineProps) {
  const [filterType, setFilterType] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEvents = events.filter((ev) => {
    if (filterType !== "all" && ev.event_type.toLowerCase() !== filterType.toLowerCase()) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        ev.title.toLowerCase().includes(q) ||
        ev.author.toLowerCase().includes(q) ||
        (ev.summary && ev.summary.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getEventIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "commit":
        return <GitCommit className="size-4 text-accent" />;
      case "pull_request":
      case "pr":
        return <GitPullRequest className="size-4 text-success" />;
      case "issue":
        return <CircleDot className="size-4 text-info" />;
      default:
        return <GitCommit className="size-4 text-text-muted" />;
    }
  };

  const getEventBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case "commit":
        return <Badge variant="accent" className="text-[10px] uppercase">Commit</Badge>;
      case "pull_request":
      case "pr":
        return <Badge variant="success" className="text-[10px] uppercase">Pull Request</Badge>;
      case "issue":
        return <Badge variant="info" className="text-[10px] uppercase">Issue</Badge>;
      default:
        return <Badge variant="neutral" className="text-[10px] uppercase">{type}</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-4xl mx-auto">
      {/* Search & Filter Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search commits, PRs, authors..."
            className="w-full rounded-lg border border-border bg-surface pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1.5">
          <Filter className="size-3.5 text-text-muted mr-1" />
          {["all", "commit", "pull_request", "issue"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                filterType === type
                  ? "bg-surface-elevated text-text-primary border border-border"
                  : "text-text-muted hover:text-text-primary"
              }`}
            >
              {type === "pull_request" ? "PRs" : type}
            </button>
          ))}
        </div>
      </div>

      {/* Chronological Timeline */}
      {filteredEvents.length === 0 ? (
        <div className="rounded-lg border border-border bg-surface p-8 text-center text-sm text-text-muted">
          No history events found matching the search or filter.
        </div>
      ) : (
        <div className="relative flex flex-col gap-4 pl-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-border">
          {filteredEvents.map((ev, idx) => (
            <div key={`${ev.identifier}-${idx}`} className="relative flex items-start gap-4">
              {/* Timeline Marker Dot */}
              <div className="absolute -left-6 top-1.5 flex size-5 items-center justify-center rounded-full bg-surface border border-border shadow">
                {getEventIcon(ev.event_type)}
              </div>

              {/* Event Card */}
              <Card className="flex flex-1 flex-col gap-2.5 p-4 bg-surface border-border transition-colors hover:border-border-strong">
                <div className="flex flex-col justify-between gap-1 sm:flex-row sm:items-center">
                  <div className="flex items-center gap-2">
                    {getEventBadge(ev.event_type)}
                    <span className="font-mono text-xs font-medium text-text-muted">
                      {ev.identifier.slice(0, 10)}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[11px] text-text-muted">
                    <span className="flex items-center gap-1">
                      <User className="size-3" />
                      {ev.author}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="size-3" />
                      {new Date(ev.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <h4 className="text-sm font-semibold text-text-primary leading-snug">
                  {ev.title}
                </h4>

                {ev.summary && (
                  <p className="text-xs text-text-secondary leading-relaxed line-clamp-3">
                    {ev.summary}
                  </p>
                )}
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
