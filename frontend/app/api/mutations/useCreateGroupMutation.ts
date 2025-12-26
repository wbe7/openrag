import {
  type UseMutationOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export interface CreateGroupRequest {
  name: string;
  description?: string;
}

export interface CreateGroupResponse {
  success: boolean;
  group_id: string;
  name: string;
  description: string;
  created_at: string;
  error?: string;
}

export const useCreateGroupMutation = (
  options?: Omit<
    UseMutationOptions<CreateGroupResponse, Error, CreateGroupRequest>,
    "mutationFn"
  >,
) => {
  const queryClient = useQueryClient();

  async function createGroup(
    variables: CreateGroupRequest,
  ): Promise<CreateGroupResponse> {
    const response = await fetch("/api/groups", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(variables),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to create group");
    }

    return data;
  }

  return useMutation({
    mutationFn: createGroup,
    onSuccess: (...args) => {
      queryClient.invalidateQueries({
        queryKey: ["groups"],
      });
      options?.onSuccess?.(...args);
    },
    onError: options?.onError,
    onSettled: options?.onSettled,
  });
};

