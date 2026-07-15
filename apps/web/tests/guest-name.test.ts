import { describe, expect, it } from "vitest";
import type { Guest } from "../src/lib/api/types";
import {
  confirmGuestName,
  guestNameError,
  isGeneratedGuestName,
  isGuestNameConfirmed,
  normalizeGuestName,
} from "../src/lib/guest-profile/guest-name";

function guest(displayName = "Explorer ABCD"): Guest {
  return {
    id: "abcd1234-guest",
    display_name: displayName,
    csrf_token: "csrf",
  };
}

function memoryStorage(): Pick<Storage, "getItem" | "setItem"> {
  const values = new Map<string, string>();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
}

describe("guest name rules", () => {
  it("normalizes Unicode compatibility characters and whitespace", () => {
    expect(normalizeGuestName("  Ｌéa\n  O’Neil  ")).toBe("Léa O’Neil");
  });

  it("accepts safe public names", () => {
    expect(guestNameError("Léa O’Neil")).toBeNull();
    expect(guestNameError("Jean-Luc 7")).toBeNull();
    expect(guestNameError("𐐀".repeat(20))).toBeNull();
  });

  it("rejects unsupported punctuation, edge punctuation, and reserved roles", () => {
    expect(guestNameError("Mira <script>")).toMatch(/letters, numbers/);
    expect(guestNameError("-Northstar")).toMatch(/letters, numbers/);
    expect(guestNameError("Webwoven Guide")).toMatch(/official Webwoven role/);
    expect(guestNameError("Admin")).toMatch(/official Webwoven role/);
  });

  it("requires explicit confirmation only for a generated alias", () => {
    const storage = memoryStorage();
    const generated = guest();

    expect(isGeneratedGuestName(generated)).toBe(true);
    expect(isGuestNameConfirmed(generated, storage)).toBe(false);

    confirmGuestName(generated, storage);

    expect(isGuestNameConfirmed(generated, storage)).toBe(true);
    expect(isGuestNameConfirmed(guest("Paper Fox"), memoryStorage())).toBe(
      true,
    );
  });
});
