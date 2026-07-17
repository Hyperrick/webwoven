import { expect, type Locator, type Page } from "@playwright/test";

export async function confirmSolo(
  page: Page,
  difficulty: "Easy" | "Normal" | "Hard" = "Normal",
): Promise<void> {
  await expect(
    page.getByRole("heading", { name: /Set the depth of the expedition/i }),
  ).toBeVisible();
  await page.getByRole("radio", { name: new RegExp(difficulty, "i") }).check();
  const introduction = page.locator(".round-intro");
  await Promise.all([
    expect(introduction).toBeVisible({ timeout: 10_000 }),
    expect(introduction.locator(".round-intro__category")).toContainText(
      `${difficulty.toLowerCase()} route`,
      { timeout: 10_000 },
    ),
    page.getByRole("button", { name: /Confirm and reveal/i }).click(),
  ]);
}

export async function startSolo(
  page: Page,
  difficulty: "Easy" | "Normal" | "Hard" = "Normal",
): Promise<void> {
  await page.goto("/play/solo");
  await confirmSolo(page, difficulty);
  await expect(page.locator(".round-intro")).toBeHidden({
    timeout: 20_000,
  });
}

export async function followTo(page: Page, entity: string): Promise<void> {
  const candidate = page
    .locator("button.map-choice, button.map-position--reachable")
    .filter({ hasText: entity })
    .first();
  await expect(
    candidate,
    `A direct map move should lead to ${entity}`,
  ).toBeVisible();
  await activateMapChoice(page, candidate);
  await expect(
    page
      .locator(".map-position--current h3, .result-hero h1")
      .filter({ hasText: entity })
      .first(),
  ).toBeVisible();
}

export async function activateMapChoice(
  page: Page,
  candidate: Locator,
): Promise<void> {
  const presentation = await page
    .locator(".game-map__viewport")
    .getAttribute("data-map-presentation");
  await candidate.click();
  if (presentation !== "constellation") return;
  const detail = page.locator("[data-mobile-choice-detail]");
  await expect(detail).toBeVisible();
  await detail.locator(".mobile-map-choice-detail__action").click();
}

export async function expectVerticalHintRail(page: Page): Promise<void> {
  const utilityRail = page.locator(".map-utility-rail");
  const hintDock = page.locator(".hint-dock");
  const mapViewport = page.locator(".game-map__viewport");
  const mapHeader = page.locator(".game-map__header");
  const mapControls = utilityRail.getByRole("toolbar", { name: "Map view" });
  const buttons = hintDock.locator(".hint-dock__actions button");
  await expect(buttons).toHaveCount(3);
  await expect(mapControls).toBeVisible();
  await expect(
    mapHeader.getByRole("button", { name: "Map controls help" }),
  ).toBeVisible();
  await expect(mapHeader.getByText(/routes? in reach/i)).toBeVisible();
  await expect(
    mapHeader.getByRole("toolbar", { name: "Map view" }),
  ).toHaveCount(0);
  await expect(
    mapViewport.locator(".map-viewport-controls--canvas"),
  ).toBeHidden();

  const [
    railBox,
    mapBox,
    headerBox,
    controlsBox,
    firstBox,
    secondBox,
    thirdBox,
  ] = await Promise.all([
    utilityRail.boundingBox(),
    mapViewport.boundingBox(),
    mapHeader.boundingBox(),
    mapControls.boundingBox(),
    buttons.nth(0).boundingBox(),
    buttons.nth(1).boundingBox(),
    buttons.nth(2).boundingBox(),
  ]);
  expect(railBox).not.toBeNull();
  expect(mapBox).not.toBeNull();
  expect(headerBox).not.toBeNull();
  expect(controlsBox).not.toBeNull();
  expect(firstBox).not.toBeNull();
  expect(secondBox).not.toBeNull();
  expect(thirdBox).not.toBeNull();
  expect(railBox!.width).toBeLessThanOrEqual(112);
  expect(railBox!.x).toBeGreaterThanOrEqual(mapBox!.x + mapBox!.width);
  expect(headerBox!.height).toBeLessThanOrEqual(80);
  expect(controlsBox!.y).toBeGreaterThanOrEqual(railBox!.y);
  expect(firstBox!.y).toBeGreaterThan(controlsBox!.y + controlsBox!.height);
  expect(
    firstBox!.y - (controlsBox!.y + controlsBox!.height),
  ).toBeLessThanOrEqual(64);
  expect(secondBox!.y).toBeGreaterThan(firstBox!.y + firstBox!.height);
  expect(thirdBox!.y).toBeGreaterThan(secondBox!.y + secondBox!.height);
  expect(thirdBox!.y + thirdBox!.height).toBeLessThan(
    railBox!.y + railBox!.height * 0.75,
  );
}
