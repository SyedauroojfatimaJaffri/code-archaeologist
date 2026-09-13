import { api } from "./api";
import type { HistorianQuestionRequest, HistorianQuestionResponse } from "@/types/historian";

export async function askHistorian(
  repositoryId: string,
  question: string
): Promise<HistorianQuestionResponse> {
  const payload: HistorianQuestionRequest = { question };
  return api.post<HistorianQuestionResponse>(
    `/repositories/${repositoryId}/questions`,
    payload
  );
}
