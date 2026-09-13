export type ConfidenceLevel = "high" | "medium" | "low";
export type ClassificationType = "verified" | "inferred" | "human_knowledge";

export interface EvidenceItem {
  source_type: "commit" | "file" | "pull_request" | "issue" | "knowledge_item" | string;
  source_id: string;
  excerpt?: string | null;
}

export interface HistorianQuestionRequest {
  question: string;
}

export interface HistorianQuestionResponse {
  answer: string;
  evidence: EvidenceItem[];
  confidence: ConfidenceLevel;
  classification: ClassificationType;
  is_refusal?: boolean;
  gap_detected?: boolean;
  gap_id?: string | null;
}
