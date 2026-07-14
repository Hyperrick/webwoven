import { expect, test, type Page } from "@playwright/test";

async function confirmSolo(
  page: Page,
  difficulty: "Easy" | "Normal" | "Hard" = "Normal",
): Promise<void> {
  await expect(
    page.getByRole("heading", { name: /Set the depth of the expedition/i }),
  ).toBeVisible();
  await page.getByRole("radio", { name: new RegExp(difficulty, "i") }).check();
  await page.getByRole("button", { name: /Confirm and reveal/i }).click();
  await expect(page.locator(".round-intro")).toBeVisible();
}

async function startSolo(
  page: Page,
  difficulty: "Easy" | "Normal" | "Hard" = "Normal",
): Promise<void> {
  await page.goto("/play/solo");
  await confirmSolo(page, difficulty);
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });
}

async function followTo(page: Page, entity: string): Promise<void> {
  const candidate = page
    .locator("button.map-choice, button.map-position--reachable")
    .filter({ hasText: entity })
    .first();
  await expect(
    candidate,
    `A direct map move should lead to ${entity}`,
  ).toBeVisible();
  await candidate.click();
  await expect(
    page
      .locator(".map-position--current h3, .result-hero h1")
      .filter({ hasText: entity })
      .first(),
  ).toBeVisible();
}

test("landing communicates the game and Codex-native build story", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "The shortest route is rarely a straight line.",
  );
  await expect(
    page.getByRole("heading", {
      name: "Everyone with an idea can become a game developer.",
    }),
  ).toBeVisible();
  await expect(page.getByText("AI at runtime")).toBeVisible();
  await expect(page.getByText("None", { exact: true })).toBeVisible();
});

test("Solo preserves visible history and guards browser Back", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Begin a route/i }).click();
  await expect(page).toHaveURL(/\/play\/solo$/);
  await confirmSolo(page);
  await expect(
    page.locator(".round-intro__category").getByRole("heading", {
      name: "Arts & Culture",
    }),
  ).toBeVisible();
  await expect(page.locator(".round-intro__card--start")).toContainText(
    "Hokusai",
  );
  await expect(page.locator(".round-intro__card--goal")).toContainText(
    "United Kingdom",
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
  await expect(
    page.locator(".map-position--goal").getByText("United Kingdom", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: /Move to The Great Wave off Kanagawa: Hokusai created The Great Wave off Kanagawa\./i,
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
      name: /Compass hint, 75 point penalty, ready/i,
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
  await expect(
    page.getByRole("button", {
      name: /Compass hint, 75 point penalty, used/i,
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
    page.getByText("Hokusai created The Great Wave off Kanagawa.", {
      exact: true,
    }),
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

test("Solo completes the four-move route and renders results", async ({
  page,
}) => {
  await startSolo(page);
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();

  for (const entity of [
    "The Great Wave off Kanagawa",
    "British Museum",
    "London",
  ]) {
    await followTo(page, entity);
  }

  const reachableGoal = page.locator("button.map-position--reachable");
  const reachableGoalCard = reachableGoal.locator(".map-position__goal-card");
  const nearbyChoice = page.locator("button.map-choice").first();
  await expect(reachableGoal).toBeVisible();
  await page.mouse.move(0, 0);
  await expect
    .poll(() =>
      reachableGoalCard.evaluate(
        (element) => getComputedStyle(element).animationName,
      ),
    )
    .toBe("reachable-goal-breathe");
  await expect(nearbyChoice).toBeVisible();
  const [goalBox, choiceBox] = await Promise.all([
    reachableGoal.boundingBox(),
    nearbyChoice.boundingBox(),
  ]);
  expect(goalBox).not.toBeNull();
  expect(choiceBox).not.toBeNull();
  expect(
    Math.abs((goalBox?.width ?? 0) - (choiceBox?.width ?? 0)),
  ).toBeLessThanOrEqual(1);
  const overlaps =
    (goalBox?.x ?? 0) < (choiceBox?.x ?? 0) + (choiceBox?.width ?? 0) &&
    (goalBox?.x ?? 0) + (goalBox?.width ?? 0) > (choiceBox?.x ?? 0) &&
    (goalBox?.y ?? 0) < (choiceBox?.y ?? 0) + (choiceBox?.height ?? 0) &&
    (goalBox?.y ?? 0) + (goalBox?.height ?? 0) > (choiceBox?.y ?? 0);
  expect(overlaps).toBe(false);

  await followTo(page, "United Kingdom");

  await expect(page).toHaveURL(/\/results$/);
  await expect
    .poll(() =>
      page
        .locator(".result-hero__seal")
        .evaluate((element) => getComputedStyle(element).animationName),
    )
    .toBe("route-stamp-land");
  await expect(page.getByRole("heading", { name: /You found/i })).toContainText(
    "United Kingdom",
  );
  await expect(page.getByText("Cartographer’s note")).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: /fictional Cartographer studying a map laid flat on a field table/i,
    }),
  ).toHaveAttribute("src", "/illustrations/cartographer.webp");

  await page.getByRole("button", { name: /Try another route/i }).click();
  await expect(page.getByRole("radio", { name: /Normal/i })).toBeChecked();
  await page.getByRole("button", { name: /Confirm and reveal/i }).click();
  await expect(page.locator(".round-intro__card--start")).toContainText(
    "The Great Wave off Kanagawa",
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

  await recovery.click();
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Back to Hokusai", exact: true }),
  ).toHaveCount(0);
  await expect(page.locator("button.map-choice")).toHaveCount(2);
  const mutedBranch = page
    .locator(".map-history-node--backtracked")
    .filter({ hasText: "Thirty-six Views of Mount Fuji" });
  await expect(mutedBranch).toBeVisible();
  await expect(mutedBranch).toHaveCSS("opacity", "0.58");
  const [currentBox, viewportBox] = await Promise.all([
    page.locator(".map-position--current").boundingBox(),
    page.locator(".game-map__viewport").boundingBox(),
  ]);
  expect(currentBox).not.toBeNull();
  expect(viewportBox).not.toBeNull();
  expect((currentBox?.x ?? 0) + (currentBox?.width ?? 0) / 2).toBeCloseTo(
    (viewportBox?.x ?? 0) + (viewportBox?.width ?? 0) / 2,
    -1,
  );
});

test("Hard selection reveals its category and endpoints before controls unlock", async ({
  page,
}) => {
  await page.goto("/play/solo");
  await confirmSolo(page, "Hard");
  await expect(page.locator(".round-intro__category")).toContainText(
    "hard route",
  );
  await expect(page.locator(".round-intro__card--start")).toContainText(
    "Hokusai",
  );
  await expect(page.locator(".round-intro__card--goal")).toContainText(
    "England",
  );
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
  await expect(page.getByRole("radio")).toHaveCount(0);
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
    "Arts & Culture · Normal",
  );
  await page.getByRole("button", { name: "I’m ready" }).click();
  await page.getByRole("button", { name: /Start relay/i }).click();
  await expect(page).toHaveURL(/\/relay\/MAPS27$/);
  await expect(page.locator(".round-intro")).toBeVisible();
  await expect(page.locator(".round-intro")).toHaveCount(0, { timeout: 7_000 });
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Live relay",
  );
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
