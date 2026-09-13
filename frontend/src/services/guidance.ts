import { api } from "./api";
import type { GuidanceRequest, GuidanceResponse } from "@/types/guidance";

export async function getGuidance(
  repositoryId: string,
  task: string
): Promise<GuidanceResponse> {
  const payload: GuidanceRequest = { task };
  return api.post<GuidanceResponse>(
    `/repositories/${repositoryId}/guidance`,
    payload
  );
}
