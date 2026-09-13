export interface KnowledgeGapItem {
  gap_id: string;
  repository_id: string;
  question: string;
  context?: string | null;
  priority: "high" | "medium" | "low" | string;
  status: "open" | "resolved" | string;
}

export interface KnowledgeGapListResponse {
  gaps: KnowledgeGapItem[];
}

export interface KnowledgeGapAnswerRequest {
  answer: string;
}

export interface KnowledgeGapAnswerResponse {
  gap_id: string;
  knowledge_item_id: string;
  status: string;
}
