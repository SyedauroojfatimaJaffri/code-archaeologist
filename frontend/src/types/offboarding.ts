export interface OffboardingQuestionItem {
  question_id: string;
  question: string;
  priority: "high" | "medium" | "low" | string;
  status: "pending" | "answered" | string;
  answer?: string | null;
}

export interface OffboardingSessionDetailResponse {
  session_id: string;
  repository_id: string;
  contributor?: string | null;
  status: string;
  questions: OffboardingQuestionItem[];
  created_at?: string | null;
}

export interface OffboardingCreateRequest {
  contributor: string;
}

export interface OffboardingCreateResponse {
  session_id: string;
  status: string;
}

export interface OffboardingAnswerRequest {
  question_id: string;
  answer: string;
}

export interface OffboardingAnswerResponse {
  question_id: string;
  status: string;
}

export interface OffboardingReportResponse {
  session_id: string;
  repository_id: string;
  contributor?: string | null;
  summary: string;
  key_decisions: string[];
  undocumented_areas: string[];
  knowledge_items: Array<Record<string, unknown>>;
  generated_at?: string | null;
}
