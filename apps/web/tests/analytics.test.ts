import { describe, expect, it } from "vitest";
import {
  analyticsAllowed,
  analyticsScriptAttributes,
  hintCount,
  movesRelativeToPar,
  sanitizeAnalyticsEvent,
} from "../src/lib/analytics/analytics";

describe("privacy-minimized analytics", () => {
  it("does not load when Do Not Track is enabled", () => {
    expect(analyticsAllowed("1")).toBe(false);
    expect(analyticsAllowed("yes")).toBe(false);
    expect(analyticsAllowed("0")).toBe(true);
    expect(analyticsAllowed(null)).toBe(true);
  });

  it("configures first-party tracking without query strings or hashes", () => {
    expect(
      analyticsScriptAttributes({
        origin: "https://stats.webwoven.org/",
        websiteId: "68f9a7b5-5d95-4a03-a40c-927b4bc24a64",
        domain: "www.webwoven.org",
      }),
    ).toEqual({
      src: "https://stats.webwoven.org/script.js",
      "data-host-url": "https://stats.webwoven.org",
      "data-website-id": "68f9a7b5-5d95-4a03-a40c-927b4bc24a64",
      "data-domains": "www.webwoven.org",
      "data-do-not-track": "true",
      "data-exclude-search": "true",
      "data-exclude-hash": "true",
    });
  });

  it("drops fields outside the fixed event contract", () => {
    const data = {
      mode: "solo",
      difficulty: "normal",
      category: "art_design",
      hint: "lens",
      session_id: "must-not-leave-the-browser",
      label: "free-form content",
    } as const;

    expect(sanitizeAnalyticsEvent("hint_used", data)).toEqual({
      mode: "solo",
      difficulty: "normal",
      category: "art_design",
      hint: "lens",
    });
  });

  it("reports only coarse completion and hint buckets", () => {
    expect(movesRelativeToPar(2, 3)).toBe("under_par");
    expect(movesRelativeToPar(3, 3)).toBe("at_par");
    expect(movesRelativeToPar(4, 3)).toBe("over_par");
    expect(movesRelativeToPar(4, null)).toBe("unknown");
    expect(hintCount(0)).toBe("none");
    expect(hintCount(1)).toBe("one");
    expect(hintCount(2)).toBe("multiple");
  });
});
