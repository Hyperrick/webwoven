import { expect, test } from "@playwright/test";
import { expectVerticalHintRail, startSolo } from "./helpers";

test("mobile Multiplayer keeps a compact roster and complete target HUD", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/lobby");
  const prompt = page.getByRole("dialog", {
    name: "What should other explorers call you?",
  });
  await prompt.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByRole("button", { name: /Create lobby/i }).click();
  await expect(
    page.getByRole("button", { name: "Share lobby MAPS27" }),
  ).toBeInViewport();
  await page.getByRole("button", { name: "I’m ready" }).click();
  await page.getByRole("button", { name: /Start game/i }).click();
  const introduction = page.locator(".round-intro");
  if (await introduction.isVisible()) {
    await expect(introduction).toBeHidden({ timeout: 20_000 });
  }

  await expect(page.locator(".race-strip__mobile-summary")).toContainText(
    "2 players",
  );
  await expect(page.locator(".race-strip__roster")).toBeHidden();
  await expect(page.locator(".round-masthead__identity")).toBeHidden();
  await expect(page.getByText("Par", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Score", { exact: true })).toBeHidden();
  await expect(page.locator(".game-map__header")).toBeHidden();
  await expect(page.getByRole("toolbar", { name: "Map view" })).toBeHidden();
  const target = page.locator(".game-metrics__target dd");
  await expect(target).toHaveText("United Kingdom");
  await expect(target).toHaveCSS("white-space", "normal");
  await expect(target).toHaveCSS("text-overflow", "clip");
  const mobileHudGeometry = await page
    .locator(".round-masthead")
    .evaluate((masthead) => {
      const bounds = masthead.getBoundingClientRect();
      const visibleMetrics = [
        ...masthead.querySelectorAll<HTMLElement>(".game-metrics > div"),
      ].filter((metric) => getComputedStyle(metric).display !== "none");
      return {
        noHorizontalOverflow: visibleMetrics.every(
          (metric) => metric.scrollWidth <= metric.clientWidth,
        ),
        insideHud: visibleMetrics.every((metric) => {
          const metricBounds = metric.getBoundingClientRect();
          return (
            metricBounds.left >= bounds.left - 1 &&
            metricBounds.right <= bounds.right + 1
          );
        }),
      };
    });
  expect(mobileHudGeometry.noHorizontalOverflow).toBe(true);
  expect(mobileHudGeometry.insideHud).toBe(true);

  await page.setViewportSize({ width: 1280, height: 720 });
  await expect(page.locator(".race-strip__roster")).toBeVisible();
  await expect(page.locator(".race-strip__roster")).toContainText(
    "mapping · 0 moves",
  );
});

test("short phone layout keeps HUD, map, and hints in one viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await startSolo(page);

  const firstMove = page.locator("button.map-choice").first();
  const secondMove = page.locator("button.map-choice").nth(1);
  const currentNode = page.locator(".map-position--current:not([inert])");
  const hintDock = page.locator(".hint-dock");
  const siteHeader = page.locator(".site-header");
  const roundMasthead = page.locator(".round-masthead");
  const mapHeader = page.locator(".game-map__header");
  const fullMapPrompt = page.getByRole("heading", {
    name: "Where do you go next?",
  });
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-layout",
    "vertical",
  );
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-presentation",
    "constellation",
  );
  await expect(page.locator(".map-position--current")).toHaveCount(1);
  await expect(page.locator("[data-mobile-choice-node]")).toHaveCount(2);
  await expect(roundMasthead).toBeInViewport();
  await expect(page.getByText("Live", { exact: true })).toBeHidden();
  await expect(page.getByText("Round active", { exact: true })).toBeAttached();
  await expect(page.getByText("Time", { exact: true })).toBeVisible();
  await expect(page.getByText("Moves", { exact: true })).toBeVisible();
  await expect(page.getByText("Par", { exact: true })).toHaveCount(0);
  await expect(
    page.locator(".game-metrics__target").getByText("Target", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".game-metrics__target dd")).toHaveText(
    "United Kingdom",
  );
  await expect(page.locator(".game-metrics__target dd")).toHaveCSS(
    "white-space",
    "normal",
  );
  await expect(page.getByText("Score", { exact: true })).toBeHidden();
  await expect(mapHeader).toBeHidden();
  await expect(fullMapPrompt).toBeHidden();
  await expect(page.getByRole("toolbar", { name: "Map view" })).toBeHidden();
  await expect(currentNode).toBeInViewport();
  await expect(firstMove).toBeVisible();
  await expect(secondMove).toBeInViewport();
  await expect(hintDock).toBeInViewport();
  await expect(hintDock).toHaveCSS("position", "relative");
  const hintButtons = hintDock.locator(".hint-dock__actions button");
  await expect(hintButtons).toHaveCount(3);
  await expect(
    page.getByRole("button", {
      name: /Compass hint.*75 point penalty.*ready/i,
    }),
  ).toBeVisible();
  const [
    headerBox,
    mastheadBox,
    mapHeaderBox,
    backBox,
    currentBox,
    moveBox,
    secondMoveBox,
    hintBox,
  ] = await Promise.all([
    siteHeader.boundingBox(),
    roundMasthead.boundingBox(),
    mapHeader.boundingBox(),
    page.locator("button.back-action").boundingBox(),
    currentNode.boundingBox(),
    firstMove.boundingBox(),
    secondMove.boundingBox(),
    hintDock.boundingBox(),
  ]);
  const viewportBox = await page.locator(".game-map__viewport").boundingBox();
  expect(headerBox).not.toBeNull();
  expect(mastheadBox).not.toBeNull();
  expect(mapHeaderBox).toBeNull();
  expect(backBox).toBeNull();
  expect(currentBox).not.toBeNull();
  expect(moveBox).not.toBeNull();
  expect(secondMoveBox).not.toBeNull();
  expect(hintBox).not.toBeNull();
  expect(viewportBox).not.toBeNull();
  expect(headerBox?.height ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(49);
  expect(mastheadBox?.height ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(
    46,
  );
  expect(viewportBox?.height ?? 0).toBeGreaterThanOrEqual(375);
  expect(viewportBox?.y ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(
    (mastheadBox?.y ?? 0) + (mastheadBox?.height ?? 0) + 1,
  );
  expect((currentBox?.y ?? 0) - (viewportBox?.y ?? 0)).toBeLessThanOrEqual(64);
  expect(moveBox?.x ?? 0).toBeGreaterThanOrEqual((viewportBox?.x ?? 0) - 1);
  expect((moveBox?.x ?? 0) + (moveBox?.width ?? 0)).toBeLessThanOrEqual(
    (viewportBox?.x ?? 0) + (viewportBox?.width ?? 0) + 1,
  );
  expect(secondMoveBox?.x ?? 0).toBeGreaterThanOrEqual(
    (viewportBox?.x ?? 0) - 1,
  );
  expect(
    (secondMoveBox?.x ?? 0) + (secondMoveBox?.width ?? 0),
  ).toBeLessThanOrEqual((viewportBox?.x ?? 0) + (viewportBox?.width ?? 0) + 1);
  expect(moveBox?.y ?? 0).toBeGreaterThan(
    (currentBox?.y ?? 0) + (currentBox?.height ?? 0),
  );
  expect(Math.abs((secondMoveBox?.y ?? 0) - (moveBox?.y ?? 0))).toBeLessThan(2);
  expect(moveBox?.height ?? 0).toBeGreaterThanOrEqual(44);
  expect(secondMoveBox?.height ?? 0).toBeGreaterThanOrEqual(44);
  const marker = firstMove.locator(".mobile-map-choice-node__marker");
  await expect(marker).toHaveCSS("width", "40px");
  await expect(marker).toHaveCSS("height", "40px");
  expect(
    (moveBox?.x ?? 0) + (moveBox?.width ?? 0) <= (secondMoveBox?.x ?? 0) ||
      (secondMoveBox?.x ?? 0) + (secondMoveBox?.width ?? 0) <=
        (moveBox?.x ?? 0),
  ).toBe(true);
  expect(hintBox?.y ?? 0).toBeGreaterThanOrEqual(
    (viewportBox?.y ?? 0) + (viewportBox?.height ?? 0) - 1,
  );
  expect(hintBox?.height ?? Number.POSITIVE_INFINITY).toBeLessThanOrEqual(56);

  const hintButtonBoxes = await hintButtons.evaluateAll((buttons) =>
    buttons.map((button) => {
      const bounds = button.getBoundingClientRect();
      return { width: bounds.width, height: bounds.height };
    }),
  );
  expect(hintButtonBoxes).toHaveLength(3);
  for (const buttonBox of hintButtonBoxes) {
    expect(buttonBox.width).toBeGreaterThanOrEqual(44);
    expect(buttonBox.height).toBeGreaterThanOrEqual(44);
  }

  const hudGeometry = await roundMasthead.evaluate((masthead) => {
    const bounds = masthead.getBoundingClientRect();
    const visibleMetrics = [
      ...masthead.querySelectorAll<HTMLElement>(".game-metrics > div"),
    ].filter((metric) => getComputedStyle(metric).display !== "none");
    return {
      values: visibleMetrics.map((metric) => {
        const value = metric.querySelector<HTMLElement>("dd");
        return value
          ? {
              fits: value.scrollWidth <= value.clientWidth,
              overflow: getComputedStyle(value).textOverflow,
            }
          : null;
      }),
      insideHud: visibleMetrics.every((metric) => {
        const metricBounds = metric.getBoundingClientRect();
        return (
          metricBounds.left >= bounds.left - 1 &&
          metricBounds.right <= bounds.right + 1
        );
      }),
    };
  });
  expect(hudGeometry.insideHud).toBe(true);
  expect(hudGeometry.values.every((value) => value?.fits)).toBe(true);
  expect(hudGeometry.values.every((value) => value?.overflow === "clip")).toBe(
    true,
  );

  const viewportHeight = await page.evaluate(() => window.innerHeight);
  const documentHeight = await page.evaluate(
    () => document.documentElement.scrollHeight,
  );
  expect(documentHeight).toBeLessThanOrEqual(viewportHeight);
  await page.mouse.wheel(0, 500);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);

  const initialCurrentNodeId =
    await currentNode.getAttribute("data-map-node-id");
  await firstMove.click();
  await expect(currentNode).toHaveAttribute(
    "data-map-node-id",
    initialCurrentNodeId ?? "",
  );
  await expect(firstMove).toHaveAttribute("aria-pressed", "true");
  await expect(firstMove).toHaveAttribute(
    "aria-label",
    /Move to The Great Wave off Kanagawa/i,
  );
  await expect(firstMove.locator("[data-mobile-choice-confirm]")).toBeVisible();
  const routeDetail = page.locator("[data-mobile-choice-detail]");
  await expect(routeDetail).toBeVisible();
  await expect(routeDetail).toContainText("The Great Wave off Kanagawa");
  await secondMove.click();
  await expect(currentNode).toHaveAttribute(
    "data-map-node-id",
    initialCurrentNodeId ?? "",
  );
  await expect(firstMove).toHaveAttribute("aria-pressed", "false");
  await expect(secondMove).toHaveAttribute("aria-pressed", "true");
  await expect(
    secondMove.locator("[data-mobile-choice-confirm]"),
  ).toBeVisible();
  await expect(routeDetail).toContainText("Thirty-six Views of Mount Fuji");
  await firstMove.click();
  await expect(currentNode).toHaveAttribute(
    "data-map-node-id",
    initialCurrentNodeId ?? "",
  );
  await expect(firstMove).toHaveAttribute("aria-pressed", "true");
  await expect(routeDetail).toContainText("The Great Wave off Kanagawa");
  await firstMove.click();
  await expect(currentNode).not.toHaveAttribute(
    "data-map-node-id",
    initialCurrentNodeId ?? "",
  );
  await expect(routeDetail).toHaveCount(0);
  await expect(currentNode).toBeInViewport();
  const activeBack = page.getByRole("button", { name: "In-game Back" });
  await expect(activeBack).toBeVisible();
  const activeBackBox = await activeBack.boundingBox();
  expect(activeBackBox?.width ?? 0).toBeGreaterThanOrEqual(44);
  expect(activeBackBox?.height ?? 0).toBeGreaterThanOrEqual(44);
  const historyBoxes = await page
    .locator(".map-history-node")
    .evaluateAll((elements) =>
      elements.map((element) => {
        const bounds = element.getBoundingClientRect();
        return { top: bounds.top, bottom: bounds.bottom };
      }),
    );
  const [nextCurrentBox, nextRouteBox] = await Promise.all([
    currentNode.boundingBox(),
    page.locator("[data-map-near-focus]").first().boundingBox(),
  ]);
  expect(historyBoxes.length).toBeGreaterThan(0);
  expect(nextCurrentBox).not.toBeNull();
  expect(nextRouteBox).not.toBeNull();
  expect(Math.max(...historyBoxes.map(({ bottom }) => bottom))).toBeLessThan(
    nextCurrentBox?.y ?? 0,
  );
  expect(nextRouteBox?.y ?? 0).toBeGreaterThan(
    (nextCurrentBox?.y ?? 0) + (nextCurrentBox?.height ?? 0),
  );
});

test("desktop layout keeps HUD, map, and hints in one viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1341, height: 868 });
  await startSolo(page);

  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-layout",
    "horizontal",
  );
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-presentation",
    "cards",
  );

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

  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-layout",
    "horizontal",
  );
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-presentation",
    "cards",
  );
  await expectVerticalHintRail(page);
  await expect(page.locator(".hint-dock")).toBeInViewport();
  await expect(
    page.getByRole("toolbar", { name: "Map view" }),
  ).toBeInViewport();

  const currentNode = page.locator(".map-position--current:not([inert])");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-layout",
    "vertical",
  );
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-presentation",
    "constellation",
  );
  await expect(page.getByText("Live", { exact: true })).toBeHidden();
  await expect(page.getByText("Round active", { exact: true })).toBeHidden();
  await expect(page.locator(".game-metrics__target dd")).toHaveText(
    "United Kingdom",
  );
  const tallPhoneMapPrompt = page.getByRole("heading", {
    name: "Where do you go next?",
  });
  await expect(tallPhoneMapPrompt).toBeHidden();
  await expect(page.locator(".game-map__header")).toBeHidden();
  await expect(page.getByRole("toolbar", { name: "Map view" })).toBeHidden();
  const [tallPhoneHeaderBox, tallPhoneMastheadBox, tallPhoneMapHeaderBox] =
    await Promise.all([
      page.locator(".site-header").boundingBox(),
      page.locator(".round-masthead").boundingBox(),
      page.locator(".game-map__header").boundingBox(),
    ]);
  expect(tallPhoneHeaderBox?.height ?? 0).toBeGreaterThan(49);
  expect(
    tallPhoneMastheadBox?.height ?? Number.POSITIVE_INFINITY,
  ).toBeLessThanOrEqual(46);
  expect(tallPhoneMapHeaderBox).toBeNull();
  await expect(currentNode).toBeInViewport();
  await page.locator("[data-mobile-choice-node]").first().click();
  await expect(page.locator("[data-mobile-choice-detail]")).toBeVisible();

  await page.setViewportSize({ width: 801, height: 1112 });
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-layout",
    "horizontal",
  );
  await expect(page.locator(".game-map__viewport")).toHaveAttribute(
    "data-map-presentation",
    "cards",
  );
  await expect(page.locator("[data-mobile-choice-detail]")).toHaveCount(0);
  await expect(page.locator(".game-map__header")).toBeVisible();
  await expect(page.getByRole("toolbar", { name: "Map view" })).toBeVisible();
  await expect(currentNode).toBeInViewport();
});
