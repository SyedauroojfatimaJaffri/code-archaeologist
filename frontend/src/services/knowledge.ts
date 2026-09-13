import { api } from "./api";
import type {
  KnowledgeGapAnswerRequest,
  KnowledgeGapAnswerResponse,
  KnowledgeGapListResponse,
} from "@/types/knowledge";

export async function getKnowledgeGaps(
  repositoryId: string
): Promise<KnowledgeGapListResponse> {
  return api.get<KnowledgeGapListResponse>(
    `/repositories/${repositoryId}/knowledge-gaps`
  );
}

export async function answerKnowledgeGap(
  repositoryId: string,
  gapId: string,
  answer: string
): Promise<KnowledgeGapAnswerResponse> {
  const payload: KnowledgeGapAnswerRequest = { answer };
  return api.post<KnowledgeGapAnswerResponse>(
    `/repositories/${repositoryId}/knowledge-gaps/${gapId}/answer`,
    payload
  );
}
