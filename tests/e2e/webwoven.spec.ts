import { expect, test } from "@playwright/test";
import {
  confirmSolo,
  expectVerticalHintRail,
  followTo,
  startSolo,
} from "./helpers";

test("Solo preserves visible history and guards browser Back", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("region", { name: "Select play mode" })
    .getByRole("button", { name: /Single player/i })
    .click();
  await expect(page).toHaveURL(/\/play\/solo$/);
  await confirmSolo(page);
  await expect(
    page.locator(".round-intro__category").getByRole("heading", {
      name: "Art & Design",
    }),
  ).toBeVisible();
  await expect(page.locator(".round-intro__card--start")).toContainText(
    "Hokusai",
  );
  await expect(page.locator(".round-intro__card--goal")).toContainText(
    "United Kingdom",
  );
  await expect(page.locator(".round-intro__endpoint-category")).toHaveText(
    "Atlas category Art & Design",
  );
  await expect(page.locator(".round-intro__mode")).toHaveText("Solo route");
  await expect(page.locator(".round-intro__registration")).not.toContainText(
    "WW /",
  );
  await expect(page.locator(".round-intro__registration")).not.toContainText(
    "SEC",
  );
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });
  const round = page.getByRole("region", { name: "Reach United Kingdom" });
  await expect(round).toBeVisible();
  await expect(round.getByRole("status")).toContainText(
    "Round active Timer running",
  );
  await expect(round).toContainText("Solo route");
  await expect(round).toContainText("Normal difficulty");
  await expect(round.getByText("Score", { exact: true })).toBeVisible();
  await expect(round.locator("dl.game-metrics")).toHaveAttribute(
    "aria-live",
    "off",
  );
  await expect(page.locator(".game-map")).toBeVisible();
  const mapHelp = page.getByRole("button", { name: "Map controls help" });
  await expect(mapHelp).toBeVisible();
  await expect(page.locator(".map-viewport__instructions")).toHaveCSS(
    "clip-path",
    "inset(50%)",
  );
  await mapHelp.click();
  await expect(page.getByRole("note", { name: "Map controls" })).toBeVisible();
  await mapHelp.click();
  const initialMapWidth = await page
    .locator(".map-viewport__world")
    .evaluate((element) => (element as HTMLElement).offsetWidth);
  await expect(page.locator(".map-board-renderer")).toHaveAttribute(
    "data-render-state",
    /ready|fallback/,
  );
  await expect(
    page.getByRole("heading", { name: "Where do you go next?" }),
  ).toBeVisible();
  await expect(page.getByText("You are here", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect current entity: Hokusai" })
    .click();
  const inspector = page.getByRole("dialog", { name: "Hokusai" });
  const inspectorBackdrop = page.getByRole("button", {
    name: "Close entity details backdrop",
  });
  await expect(inspectorBackdrop).toBeVisible();
  await expect(inspectorBackdrop).toHaveCSS("backdrop-filter", /blur\(5px\)/);
  await expect(
    inspector.getByRole("link", {
      name: "Read Hokusai on Wikipedia (opens in a new tab)",
    }),
  ).toHaveAttribute("href", "https://en.wikipedia.org/wiki/Hokusai");
  await inspector.getByRole("button", { name: "Close entity details" }).click();
  await expect(
    page.locator(".map-position--goal").getByText("United Kingdom", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: /Move to The Great Wave off Kanagawa: The Great Wave off Kanagawa is a notable work by Hokusai\./i,
    }),
  ).toBeVisible();
  await expect(
    page.locator(".map-choice__number, .map-choice__go"),
  ).toHaveCount(0);
  await expect(page.getByText("notable work", { exact: true })).toHaveCount(0);
  await expect(page.locator(".destination-brief, .relation-index")).toHaveCount(
    0,
  );

  await page
    .getByRole("button", {
      name: /Compass hint.*75 point penalty.*ready/i,
    })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Which route should the Compass check?",
    }),
  ).toBeVisible();
  await page
    .locator("button.map-choice")
    .filter({ hasText: "The Great Wave off Kanagawa" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Latest hint", { exact: true })).toBeVisible();
  await expect(page.locator(".map-choice--promising")).toContainText(
    "PROMISING ROUTE",
  );
  await expect(page.locator(".hint-dock__message")).toContainText(
    "The Great Wave off Kanagawa",
  );
  await expect(
    page.getByRole("button", {
      name: /Compass hint.*75 point penalty.*used/i,
    }),
  ).toBeDisabled();

  await followTo(page, "The Great Wave off Kanagawa");
  await expect(page.locator(".game-map__trail li")).toHaveCount(2);
  await expect(page.locator(".map-history-node--discarded")).toHaveCount(1);
  await expect(page.locator(".map-history-node--breadcrumb")).toContainText(
    "Hokusai",
  );
  const widenedMapWidth = await page
    .locator(".map-viewport__world")
    .evaluate((element) => (element as HTMLElement).offsetWidth);
  expect(widenedMapWidth).toBeGreaterThan(initialMapWidth);
  await expect(page.getByText("Last move", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      "The Great Wave off Kanagawa is a notable work by Hokusai.",
      {
        exact: true,
      },
    ),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("alertdialog", { name: /Your map is still unfinished/i }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Keep exploring" }).click();
  await expect(page).toHaveURL(/\/play\/solo$/);

  await page.getByRole("button", { name: /In-game Back/i }).click();
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".game-map__trail li")).toHaveCount(3);
  await expect(
    page.locator(".map-history-node--discarded").filter({
      hasText: "The Great Wave off Kanagawa",
    }),
  ).toBeVisible();
  const retracedMapWidth = await page
    .locator(".map-viewport__world")
    .evaluate((element) => (element as HTMLElement).offsetWidth);
  expect(retracedMapWidth).toBeGreaterThan(widenedMapWidth);
  await expect(page.getByText(/retraced the route to Hokusai/i)).toBeVisible();
});

test("Lens marks one exact card and Compass identifies a shared-relation dead end", async ({
  page,
}) => {
  await startSolo(page, "Hard");
  const wave = page
    .locator("button.map-choice")
    .filter({ hasText: "The Great Wave off Kanagawa" });
  const series = page
    .locator("button.map-choice")
    .filter({ hasText: "Thirty-six Views of Mount Fuji" });

  await page.getByRole("button", { name: /Lens hint.*ready/i }).click();
  await expect(wave).toHaveClass(/map-choice--promising/);
  await expect(wave.locator(".map-choice__hint")).toHaveText("PROMISING ROUTE");
  await expect(series).not.toHaveClass(/map-choice--promising/);
  await expect(page.locator(".hint-dock__message")).toContainText(
    "The Great Wave off Kanagawa",
  );

  await page.getByRole("button", { name: /Compass hint.*ready/i }).click();
  await series.click();
  await expect(series).toHaveClass(/map-choice--dead-end/);
  await expect(series.locator(".map-choice__hint")).toHaveText("DEAD END");
  await expect(page.locator(".hint-dock__message")).toContainText(
    "Thirty-six Views of Mount Fuji is a dead end from here",
  );
});

test("an exhausted branch offers a contextual Back action", async ({
  page,
}) => {
  await startSolo(page);
  await followTo(page, "Thirty-six Views of Mount Fuji");

  await expect(
    page.getByRole("heading", { name: "This branch ends here" }),
  ).toBeVisible();
  const recovery = page.getByRole("button", {
    name: "Back to Hokusai",
    exact: true,
  });
  await expect(recovery).toBeVisible();
  await expect(
    page.getByText("Counts as 1 move", { exact: true }),
  ).toBeVisible();
  const mapWorld = page.locator(".map-viewport__world");
  const cameraBeforeRecovery = await mapWorld.evaluate(
    (element) => getComputedStyle(element).transform,
  );

  await recovery.click();
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Back to Hokusai", exact: true }),
  ).toHaveCount(0);
  await expect(page.locator("button.map-choice")).toHaveCount(2);
  await expect(
    page
      .locator(".map-history-node--backtracked")
      .filter({ hasText: "Thirty-six Views of Mount Fuji" }),
  ).toHaveCount(0);
  await expect
    .poll(() =>
      mapWorld.evaluate((element) => getComputedStyle(element).transform),
    )
    .toBe(cameraBeforeRecovery);
  await expect(
    page.locator(".map-position--current").filter({ hasText: "Hokusai" }),
  ).toBeVisible();
  await expect(page.locator(".game-map__dead-end")).toHaveCount(0);
});

test("Hard selection reveals its category and endpoints before controls unlock", async ({
  page,
}) => {
  await page.goto("/play/solo");
  await confirmSolo(page, "Hard");
  await expect(page.locator(".round-intro__card--start")).toContainText(
    "Hokusai",
  );
  await expect(page.locator(".round-intro__card--goal")).toContainText(
    "England",
  );
  await expect(
    page.locator(".round-intro__artwork.endpoint-artwork--fit-contain"),
  ).toHaveCount(2);
  await expect(
    page.locator(".round-intro__artwork .endpoint-artwork__backdrop"),
  ).toHaveCount(2);
  await expect
    .poll(() =>
      page
        .locator(".round-intro__artwork .endpoint-artwork__image")
        .evaluateAll((images) =>
          images.every(
            (image) => getComputedStyle(image).objectFit === "contain",
          ),
        ),
    )
    .toBe(true);
  await expect(page.locator(".game-page__play")).toHaveAttribute("inert", "");
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });
  await expect(page.locator(".game-page__play")).not.toHaveAttribute(
    "inert",
    "",
  );
});

test("Daily and Live Relay expose their complete entry states", async ({
  page,
}) => {
  await page.goto("/play/daily");
  const dailyPrompt = page.getByRole("dialog", {
    name: "What should other explorers call you?",
  });
  await expect(dailyPrompt).toBeVisible();
  await expect(dailyPrompt).toContainText("Daily connection");
  await expect(dailyPrompt).toContainText("today’s leaderboard");
  await dailyPrompt
    .getByRole("button", { name: "Continue", exact: true })
    .click();
  await expect(page.getByRole("radio")).toHaveCount(0);
  await expect(page.locator(".round-intro__mode")).toHaveText(
    "Daily connection",
  );
  await expect(page.locator(".round-intro__category")).toContainText(
    "normal route",
  );
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Daily connection",
  );

  await page.goto("/relay");
  await page.getByRole("button", { name: /Create relay/i }).click();
  await expect(page.getByText("MAPS27", { exact: true })).toBeVisible();
  await expect(page.getByText("2 / 4", { exact: true })).toBeVisible();
  await expect(page.locator(".room-route-stamp")).toContainText(
    "Art & Design · Normal",
  );
  await page.getByRole("button", { name: "I’m ready" }).click();
  await page.getByRole("button", { name: /Start relay/i }).click();
  await expect(page).toHaveURL(/\/relay\/MAPS27$/);
  await expect(page.locator(".round-intro")).toBeVisible();
  await expect(page.locator(".round-intro__mode")).toHaveText("Live relay");
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Live relay",
  );

  for (const entity of [
    "The Great Wave off Kanagawa",
    "British Museum",
    "London",
    "United Kingdom",
  ]) {
    await followTo(page, entity);
  }
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.locator(".result-hero__copy")).toContainText(
    "Live relay complete",
  );
  await page
    .getByRole("button", { name: /Create or join another Relay/i })
    .click();
  await expect(page).toHaveURL(/\/relay$/);
  await expect(
    page.getByRole("heading", { name: /One atlas.*Several instincts/i }),
  ).toBeVisible();
});

test("a named Daily player is ranked from their completed route", async ({
  page,
}) => {
  await page.goto("/play/daily");
  const prompt = page.getByRole("dialog", {
    name: "What should other explorers call you?",
  });
  await prompt.getByLabel("Public explorer name").fill("Paper Fox");
  await prompt.getByRole("button", { name: "Continue", exact: true }).click();
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });

  for (const entity of [
    "The Great Wave off Kanagawa",
    "British Museum",
    "London",
    "United Kingdom",
  ]) {
    await followTo(page, entity);
  }

  await expect(page).toHaveURL(/\/results$/);
  await expect(page.locator(".result-hero__copy")).toContainText(
    "Daily connection complete",
  );
  const current = page.locator(".leaderboard__you");
  await expect(current).toContainText("Paper Fox");
  await expect(current.getByText("You", { exact: true })).toBeVisible();
  await expect(current.locator("span")).toHaveText("1");
  await expect(current).toContainText("4 moves");
  await expect(page.locator(".leaderboard__position")).toHaveCount(0);
});

test("Settings edits the public name and locks it during a Relay", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Open settings/i }).click();
  const input = page.getByLabel("Public explorer name");
  await input.fill("Atlas Reader");
  await page.getByRole("button", { name: "Save name" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Explorer name updated.",
  );
  await page
    .getByRole("dialog", { name: "Settings" })
    .getByRole("button", { name: "Close settings" })
    .click();

  await page
    .getByRole("region", { name: "Select play mode" })
    .getByRole("button", { name: /Multiplayer/i })
    .click();
  await page.getByRole("button", { name: /Create relay/i }).click();
  await page.getByRole("button", { name: /Open settings/i }).click();
  await expect(page.getByLabel("Public explorer name")).toBeDisabled();
  await expect(
    page.getByText(/name is locked during a live Relay/i),
  ).toBeVisible();
});

test("settings apply the reduced motion preference", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Open settings/i }).click();
  await page.getByLabel("Reduce motion").check();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "reduced");
  await expect(page.getByLabel("High contrast")).toHaveCount(0);
  await expect(page.locator("html")).not.toHaveAttribute("data-contrast", /.+/);
});

test("map stays playable when WebGL is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      configurable: true,
      value: () => null,
    });
  });
  await page.goto("/play/solo");
  await confirmSolo(page);
  await expect(page.locator(".round-intro--static")).toBeVisible();
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });

  await expect(page.locator(".map-board-renderer")).toHaveAttribute(
    "data-render-state",
    "fallback",
  );
  await expect(page.locator(".map-board-fallback__link")).toHaveCount(2);
  await expect(page.locator(".map-board-fallback__node")).toHaveCount(2);
  await expect(page.locator(".map-board-fallback__node--choice")).toHaveCount(
    0,
  );
  await expect(page.locator("button.map-choice").first()).toBeVisible();
});

test("short phone layout keeps HUD, map, and hints in one viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await startSolo(page);

  const firstMove = page.locator("button.map-choice").first();
  const hintDock = page.locator(".hint-dock");
  await expect(page.locator(".round-masthead")).toBeInViewport();
  await expect(
    page.getByRole("toolbar", { name: "Map view" }),
  ).toBeInViewport();
  await expect(firstMove).toBeVisible();
  await expect(hintDock).toBeInViewport();
  await expect(hintDock).toHaveCSS("position", "relative");
  const [moveBox, hintBox] = await Promise.all([
    firstMove.boundingBox(),
    hintDock.boundingBox(),
  ]);
  const viewportBox = await page.locator(".game-map__viewport").boundingBox();
  expect(moveBox).not.toBeNull();
  expect(hintBox).not.toBeNull();
  expect(viewportBox).not.toBeNull();
  expect(moveBox?.x ?? 0).toBeGreaterThanOrEqual((viewportBox?.x ?? 0) - 1);
  expect((moveBox?.x ?? 0) + (moveBox?.width ?? 0)).toBeLessThanOrEqual(
    (viewportBox?.x ?? 0) + (viewportBox?.width ?? 0) + 1,
  );
  expect(hintBox?.y ?? 0).toBeGreaterThanOrEqual(
    (moveBox?.y ?? 0) + (moveBox?.height ?? 0),
  );

  const viewportHeight = await page.evaluate(() => window.innerHeight);
  const documentHeight = await page.evaluate(
    () => document.documentElement.scrollHeight,
  );
  expect(documentHeight).toBeLessThanOrEqual(viewportHeight);
  await page.mouse.wheel(0, 500);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
});

test("desktop layout keeps HUD, map, and hints in one viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1341, height: 868 });
  await startSolo(page);

  const hintDock = page.locator(".hint-dock");
  await expect(page.locator(".round-masthead")).toBeInViewport();
  await expect(
    page.getByRole("toolbar", { name: "Map view" }),
  ).toBeInViewport();
  await expect(hintDock).toBeInViewport();
  await expectVerticalHintRail(page);

  const compass = page.getByRole("button", {
    name: /Compass hint.*75 point penalty.*ready/i,
  });
  const compassHelp = page.getByRole("tooltip", {
    name: "Check one route: promising, longer, or a dead end.",
  });
  await expect(compassHelp).toBeHidden();
  await compass.focus();
  await expect(compassHelp).toBeVisible();

  const assertNoPageScroll = async (): Promise<void> => {
    const viewportHeight = await page.evaluate(() => window.innerHeight);
    const documentHeight = await page.evaluate(
      () => document.documentElement.scrollHeight,
    );
    expect(documentHeight).toBeLessThanOrEqual(viewportHeight);
  };

  await assertNoPageScroll();
  const mapBoxBeforeHint = await page.locator(".game-map").boundingBox();
  await page.getByRole("button", { name: /Lens hint.*ready/i }).click();
  await expect(page.locator(".hint-dock__message")).toBeInViewport();
  const mapBoxAfterHint = await page.locator(".game-map").boundingBox();
  expect(mapBoxBeforeHint).not.toBeNull();
  expect(mapBoxAfterHint).not.toBeNull();
  expect(mapBoxAfterHint!.width).toBe(mapBoxBeforeHint!.width);
  expect(mapBoxAfterHint!.height).toBe(mapBoxBeforeHint!.height);
  await assertNoPageScroll();
  await page.mouse.wheel(0, 500);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
});

test("tablet layout uses the compact vertical hint rail", async ({ page }) => {
  await page.setViewportSize({ width: 801, height: 1112 });
  await startSolo(page);

  await expectVerticalHintRail(page);
  await expect(page.locator(".hint-dock")).toBeInViewport();
  await expect(
    page.getByRole("toolbar", { name: "Map view" }),
  ).toBeInViewport();
});
