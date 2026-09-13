export interface GuidanceStep {
  order?: number;
  title: string;
  files: string[];
  reasoning: string;
}

export interface GuidanceRequest {
  task: string;
}

export interface GuidanceResponse {
  task: string;
  steps: GuidanceStep[];
}
