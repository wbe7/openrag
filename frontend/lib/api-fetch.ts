/**
 * Enhanced fetch wrapper with default headers for cloud deployments.
 * Ensures all API requests include necessary headers that may be required
 * by reverse proxies, load balancers, or authentication layers.
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const defaultHeaders: HeadersInit = {
    Accept: "*/*",
    "Content-Type": "application/json",
  };

  const mergedInit: RequestInit = {
    credentials: "same-origin",
    ...init,
    headers: {
      ...defaultHeaders,
      ...init?.headers,
    },
  };

  return fetch(input, mergedInit);
}
