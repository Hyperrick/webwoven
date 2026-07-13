export interface ApiResponseContext {
  method: string;
  path: string;
}

export async function readJsonResponse<T>(
  response: Response,
  context: ApiResponseContext,
): Promise<T> {
  const body = await response.text();
  if (!body.trim()) {
    throw protocolError("an empty", response, context);
  }

  const mediaType = response.headers
    .get("Content-Type")
    ?.split(";", 1)[0]
    .trim()
    .toLowerCase();
  if (!mediaType || !isJsonMediaType(mediaType)) {
    throw protocolError("a non-JSON", response, context);
  }

  try {
    return JSON.parse(body) as T;
  } catch {
    throw protocolError("an unreadable", response, context);
  }
}

export async function readErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const body = await response.text();
  if (!body.trim()) return fallback;
  try {
    const payload = JSON.parse(body) as { message?: unknown };
    return typeof payload.message === "string" && payload.message
      ? payload.message
      : fallback;
  } catch {
    return fallback;
  }
}

function isJsonMediaType(mediaType: string): boolean {
  return mediaType === "application/json" || mediaType.endsWith("+json");
}

function protocolError(
  problem: string,
  response: Response,
  context: ApiResponseContext,
): Error {
  return new Error(
    `The atlas received ${problem} API response (${response.status} ${context.method} ${context.path}). Reload the page and try again.`,
  );
}
