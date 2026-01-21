import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KnowledgeFilter } from "../queries/useGetFiltersSearchQuery";
import { apiFetch } from "@/lib/api-fetch";

export interface CreateFilterRequest {
  name: string;
  description?: string;
  queryData: string; // stringified ParsedQueryData
}

export interface CreateFilterResponse {
  success: boolean;
  filter: KnowledgeFilter;
  message?: string;
}

async function createFilter(
  data: CreateFilterRequest,
): Promise<CreateFilterResponse> {
  const response = await apiFetch("/api/knowledge-filter", {
    method: "POST",
    body: JSON.stringify({
      name: data.name,
      description: data.description ?? "",
      queryData: data.queryData,
    }),
  });

  const json = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMessage =
      (json && (json.error as string)) || "Failed to create knowledge filter";
    throw new Error(errorMessage);
  }

  return json as CreateFilterResponse;
}

export const useCreateFilter = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createFilter,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-filters"] });
    },
  });
};
