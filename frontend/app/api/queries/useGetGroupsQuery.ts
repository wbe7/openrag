import { type UseQueryOptions, useQuery } from "@tanstack/react-query";

export interface Group {
  group_id: string;
  name: string;
  description: string;
  created_at: string;
}

export interface GetGroupsResponse {
  success: boolean;
  groups: Group[];
}

export const useGetGroupsQuery = (
  options?: Omit<UseQueryOptions<GetGroupsResponse>, "queryKey" | "queryFn">,
) => {
  async function getGroups(): Promise<GetGroupsResponse> {
    const response = await fetch("/api/groups");
    if (response.ok) {
      return await response.json();
    }
    throw new Error("Failed to fetch groups");
  }

  return useQuery({
    queryKey: ["groups"],
    queryFn: getGroups,
    ...options,
  });
};

