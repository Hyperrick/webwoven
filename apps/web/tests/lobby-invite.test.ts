import { describe, expect, it, vi } from "vitest";
import {
  lobbyInviteUrl,
  shareLobbyInvite,
  type LobbyShareEnvironment,
} from "../src/lib/sharing/lobby-invite";

const origin = "https://www.webwoven.org";

function environment(
  overrides: Partial<LobbyShareEnvironment> = {},
): LobbyShareEnvironment {
  return { origin, ...overrides };
}

describe("lobby invitations", () => {
  it("builds the canonical normalized lobby join URL", () => {
    expect(lobbyInviteUrl(" maps27 ", origin)).toBe(
      "https://www.webwoven.org/relay/MAPS27/join",
    );
  });

  it("opens the native share sheet with the host and deep link", async () => {
    const share = vi.fn(async () => undefined);

    await expect(
      shareLobbyInvite(
        { code: "MAPS27", hostDisplayName: "Host Atlas" },
        environment({ share }),
      ),
    ).resolves.toEqual({
      status: "shared",
      url: "https://www.webwoven.org/relay/MAPS27/join",
    });
    expect(share).toHaveBeenCalledWith({
      title: "Join a Webwoven lobby",
      text: "Host Atlas invited you to race through the Webwoven atlas.",
      url: "https://www.webwoven.org/relay/MAPS27/join",
    });
  });

  it("does not copy when the player cancels native sharing", async () => {
    const copy = vi.fn(async () => undefined);
    const share = vi.fn(async () => {
      throw { name: "AbortError" };
    });

    const result = await shareLobbyInvite(
      { code: "MAPS27", hostDisplayName: "Host Atlas" },
      environment({ share, copy }),
    );

    expect(result.status).toBe("cancelled");
    expect(copy).not.toHaveBeenCalled();
  });

  it("copies the deep link when native sharing is unavailable", async () => {
    const copy = vi.fn(async () => undefined);

    const result = await shareLobbyInvite(
      { code: "MAPS27", hostDisplayName: "Host Atlas" },
      environment({ copy }),
    );

    expect(result.status).toBe("copied");
    expect(copy).toHaveBeenCalledWith(
      "https://www.webwoven.org/relay/MAPS27/join",
    );
  });

  it("falls back to copying when the native share sheet fails", async () => {
    const copy = vi.fn(async () => undefined);
    const share = vi.fn(async () => {
      throw new Error("Share target unavailable");
    });

    const result = await shareLobbyInvite(
      { code: "MAPS27", hostDisplayName: "Host Atlas" },
      environment({ share, copy }),
    );

    expect(result.status).toBe("copied");
    expect(copy).toHaveBeenCalledWith(
      "https://www.webwoven.org/relay/MAPS27/join",
    );
  });

  it("returns a selectable URL when browser sharing and copying fail", async () => {
    const result = await shareLobbyInvite(
      { code: "MAPS27", hostDisplayName: "Host Atlas" },
      environment(),
    );

    expect(result).toEqual({
      status: "manual",
      url: "https://www.webwoven.org/relay/MAPS27/join",
    });
  });
});
