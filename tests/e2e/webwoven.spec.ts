import { expect, test, type Page } from "@playwright/test";

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
    .locator(".game-map__viewport")
    .evaluate((element) => element.scrollWidth);
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
      name: /Go: Hokusai created The Great Wave off Kanagawa\./i,
    }),
  ).toBeVisible();
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
    .locator(".game-map__viewport")
    .evaluate((element) => element.scrollWidth);
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
    page.locator(".map-history-node--breadcrumb").filter({
      hasText: "The Great Wave off Kanagawa",
    }),
  ).toBeVisible();
  const retracedMapWidth = await page
    .locator(".game-map__viewport")
    .evaluate((element) => element.scrollWidth);
  expect(retracedMapWidth).toBeGreaterThan(widenedMapWidth);
  await expect(page.getByText(/retraced the route to Hokusai/i)).toBeVisible();
});

test("Solo completes the four-move route and renders results", async ({
  page,
}) => {
  await page.goto("/play/solo");
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();

  for (const entity of [
    "The Great Wave off Kanagawa",
    "British Museum",
    "London",
    "United Kingdom",
  ]) {
    await followTo(page, entity);
  }

  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("heading", { name: /You found/i })).toContainText(
    "United Kingdom",
  );
  await expect(page.getByText("Cartographer’s note")).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: /fictional Cartographer studying a map laid flat on a field table/i,
    }),
  ).toHaveAttribute("src", "/illustrations/cartographer.webp");
});

test("Daily and Live Relay expose their complete entry states", async ({
  page,
}) => {
  await page.goto("/play/daily");
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Daily connection",
  );

  await page.goto("/relay");
  await page.getByRole("button", { name: /Create relay/i }).click();
  await expect(page.getByText("MAPS27", { exact: true })).toBeVisible();
  await expect(page.getByText("2 / 4", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "I’m ready" }).click();
  await page.getByRole("button", { name: /Start relay/i }).click();
  await expect(page).toHaveURL(/\/relay\/MAPS27$/);
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Live relay",
  );
});

test("settings apply reduced motion and high contrast preferences", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Open settings/i }).click();
  await page.getByLabel("Reduce motion").check();
  await page.getByLabel("High contrast").check();
  await expect(page.locator("html")).toHaveAttribute("data-motion", "reduced");
  await expect(page.locator("html")).toHaveAttribute("data-contrast", "high");
});

test("map stays playable when WebGL is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      configurable: true,
      value: () => null,
    });
  });
  await page.goto("/play/solo");

  await expect(page.locator(".map-board-renderer")).toHaveAttribute(
    "data-render-state",
    "fallback",
  );
  await expect(page.locator(".map-board-fallback__link")).toHaveCount(2);
  await expect(page.locator(".map-board-fallback__node")).toHaveCount(4);
  await expect(page.locator("button.map-choice").first()).toBeVisible();
});

test("short phone layout keeps hint tools below playable moves", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await page.goto("/play/solo");

  const firstMove = page.locator("button.map-choice").first();
  const hintDock = page.locator(".hint-dock");
  await expect(firstMove).toBeVisible();
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
});
