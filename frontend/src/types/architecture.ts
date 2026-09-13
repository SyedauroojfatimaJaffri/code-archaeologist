export interface DependencyNode {
  id: string;
  name: string;
  type: "file" | "module" | "class" | "function" | string;
  path?: string;
}

export interface DependencyEdge {
  id: string;
  source: string;
  target: string;
  type: "imports" | "calls" | "inherits" | "depends_on" | string;
}

export interface ArchitectureData {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
}
