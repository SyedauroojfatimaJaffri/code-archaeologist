import { useState } from "react";
import { Network, Box, Layers, Search } from "lucide-react";
import type { ArchitectureData, DependencyNode } from "@/types/architecture";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface DependencyGraphProps {
  data: ArchitectureData;
}

export function DependencyGraph({ data }: DependencyGraphProps) {
  const [selectedNode, setSelectedNode] = useState<DependencyNode | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredNodes = data.nodes.filter((node) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      node.name.toLowerCase().includes(q) ||
      (node.path && node.path.toLowerCase().includes(q))
    );
  });

  const connectedEdges = selectedNode
    ? data.edges.filter(
        (e) => e.source === selectedNode.id || e.target === selectedNode.id
      )
    : [];

  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-6xl mx-auto">
      {/* Search Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div className="flex items-center gap-2">
          <Layers className="size-5 text-accent" />
          <h3 className="text-base font-semibold text-text-primary">
            Architecture & Dependency Topology
          </h3>
        </div>

        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search module or class..."
            className="w-full rounded-lg border border-border bg-surface pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:border-accent focus:outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Node Grid Explorer */}
        <div className="lg:col-span-2 flex flex-col gap-3">
          <span className="text-xs font-medium text-text-muted">
            Codebase Modules & Entities ({filteredNodes.length})
          </span>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 max-h-[500px] overflow-y-auto pr-1">
            {filteredNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <button
                  key={node.id}
                  type="button"
                  onClick={() => setSelectedNode(node)}
                  className={`flex flex-col items-start gap-2 rounded-lg border p-3.5 text-left transition-all ${
                    isSelected
                      ? "border-accent bg-surface-elevated ring-1 ring-accent"
                      : "border-border bg-surface hover:border-border-strong hover:bg-surface-elevated"
                  }`}
                >
                  <div className="flex w-full items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-text-primary truncate">
                      {node.name}
                    </span>
                    <Badge variant="neutral" className="text-[10px] uppercase">
                      {node.type}
                    </Badge>
                  </div>
                  {node.path && (
                    <span className="font-mono text-[11px] text-text-muted truncate w-full">
                      {node.path}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Node Inspector Panel */}
        <Card className="flex flex-col gap-4 p-5 bg-surface border-border h-fit">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <Box className="size-4 text-accent" />
            <h4 className="text-sm font-semibold text-text-primary">
              Dependency Inspector
            </h4>
          </div>

          {selectedNode ? (
            <div className="flex flex-col gap-4 animate-fade-in">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted">
                  Selected Entity
                </span>
                <h5 className="font-mono text-sm font-bold text-text-primary mt-0.5">
                  {selectedNode.name}
                </h5>
                <p className="font-mono text-xs text-text-secondary mt-0.5">
                  {selectedNode.path ?? "Root module"}
                </p>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                  Connected Edges ({connectedEdges.length})
                </span>
                {connectedEdges.length === 0 ? (
                  <p className="text-xs text-text-muted">No explicit recorded dependencies.</p>
                ) : (
                  <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
                    {connectedEdges.map((edge) => (
                      <div
                        key={edge.id}
                        className="flex items-center justify-between rounded border border-border bg-surface-elevated p-2 text-xs"
                      >
                        <span className="font-mono text-text-primary truncate max-w-[100px]">
                          {edge.source === selectedNode.id ? edge.target : edge.source}
                        </span>
                        <Badge variant="accent" className="text-[9px]">
                          {edge.type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-6 text-center text-xs text-text-muted">
              <Network className="size-8 text-text-muted mb-2 opacity-50" />
              <span>Select any module or component on the left to inspect its dependency connections.</span>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
