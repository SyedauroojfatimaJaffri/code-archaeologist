export interface RiskItem {
  file_id: string;
  file_path?: string | null;
  score: number;
  signals: Record<string, unknown>;
  explanation?: string | null;
}

export interface RiskResponse {
  risks: RiskItem[];
}
