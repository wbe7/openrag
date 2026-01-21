import {
  type UseMutationOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-fetch";

interface OnboardingRollbackResponse {
  message: string;
}

export const useOnboardingRollbackMutation = (
  options?: Omit<
    UseMutationOptions<OnboardingRollbackResponse, Error, void>,
    "mutationFn"
  >,
) => {
  const queryClient = useQueryClient();

  async function rollbackOnboarding(): Promise<OnboardingRollbackResponse> {
    const response = await apiFetch("/api/onboarding/rollback", {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Failed to rollback onboarding");
    }

    return response.json();
  }

  return useMutation({
    mutationFn: rollbackOnboarding,
    onSettled: () => {
      // Invalidate settings query to refetch updated data
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    ...options,
  });
};

