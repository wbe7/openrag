/**
 * Enhanced fetch wrapper with default headers for cloud deployments.
 * Ensures all API requests include necessary headers that may be required
 * by reverse proxies, load balancers, or authentication layers.
 * Includes timeout protection to detect dead connections.
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const defaultHeaders: HeadersInit = {
    Accept: "*/*",
    "Content-Type": "application/json",
    // Force new connection per request to avoid HTTP/2 multiplexing issues
    Connection: "close",
  };

  const mergedInit: RequestInit = {
    credentials: "same-origin",
    ...init,
    headers: {
      ...defaultHeaders,
      ...init?.headers,
    },
  };

  // Add timeout to detect dead connections (30s default)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);

  try {
    const response = await fetch(input, {
      ...mergedInit,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Request timeout - connection may be dead");
    }
    throw error;
  }
}
