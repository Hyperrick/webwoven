export type LobbyShareStatus = "shared" | "copied" | "cancelled" | "manual";

export interface LobbyShareResult {
  status: LobbyShareStatus;
  url: string;
}

export interface LobbyShareEnvironment {
  origin: string;
  share?: (data: ShareData) => Promise<void>;
  copy?: (value: string) => Promise<void>;
}

interface LobbyShareInput {
  code: string;
  hostDisplayName: string;
}

export function lobbyInviteUrl(code: string, origin: string): string {
  const normalizedCode = code.trim().toUpperCase();
  return new URL(
    `/lobby/${encodeURIComponent(normalizedCode)}/join`,
    origin,
  ).toString();
}

export async function shareLobbyInvite(
  input: LobbyShareInput,
  environment: LobbyShareEnvironment = browserShareEnvironment(),
): Promise<LobbyShareResult> {
  const url = lobbyInviteUrl(input.code, environment.origin);
  const data: ShareData = {
    title: "Join a Webwoven lobby",
    text: `${input.hostDisplayName} invited you to race through the Webwoven atlas.`,
    url,
  };

  if (environment.share) {
    try {
      // This call intentionally happens before the first await so the browser's
      // transient user activation is still available to the native share sheet.
      const share = environment.share(data);
      await share;
      return { status: "shared", url };
    } catch (error) {
      if (isAbortError(error)) return { status: "cancelled", url };
    }
  }

  if (environment.copy) {
    try {
      await environment.copy(url);
      return { status: "copied", url };
    } catch {
      // A selectable URL remains available when clipboard access is denied.
    }
  }

  return { status: "manual", url };
}

function browserShareEnvironment(): LobbyShareEnvironment {
  return {
    origin: window.location.origin,
    share:
      typeof navigator.share === "function"
        ? navigator.share.bind(navigator)
        : undefined,
    copy:
      typeof navigator.clipboard?.writeText === "function"
        ? navigator.clipboard.writeText.bind(navigator.clipboard)
        : undefined,
  };
}

function isAbortError(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "name" in error &&
    error.name === "AbortError"
  );
}
