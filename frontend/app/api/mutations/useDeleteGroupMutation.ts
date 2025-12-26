import {
  type UseMutationOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export interface DeleteGroupRequest {
  group_id: string;
}

export interface DeleteGroupResponse {
  success: boolean;
  error?: string;
}

export const useDeleteGroupMutation = (
  options?: Omit<
    UseMutationOptions<DeleteGroupResponse, Error, DeleteGroupRequest>,
    "mutationFn"
  >,
) => {
  const queryClient = useQueryClient();

  async function deleteGroup(
    variables: DeleteGroupRequest,
  ): Promise<DeleteGroupResponse> {
    const response = await fetch(`/api/groups/${variables.group_id}`, {
      method: "DELETE",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to delete group");
    }

    return data;
  }

  return useMutation({
    mutationFn: deleteGroup,
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

