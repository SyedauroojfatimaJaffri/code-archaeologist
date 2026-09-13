import { api } from "./api";
import type { RiskResponse } from "@/types/risk";

export async function getRisks(repositoryId: string): Promise<RiskResponse> {
  return api.get<RiskResponse>(`/repositories/${repositoryId}/risks`);
}
