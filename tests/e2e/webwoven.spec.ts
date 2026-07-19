import { expect, test } from "@playwright/test";
import { activateMapChoice, confirmSolo, followTo, startSolo } from "./helpers";

test("Solo preserves visible history and guards browser Back", async ({
  page,
}) => {
  test.setTimeout(60_000);
  await page.goto("/");
  await page
    .getByRole("region", { name: "Select play mode" })
    .getByRole("button", { name: /Single player/i })
    .click();
  await expect(page).toHaveURL(/\/play\/solo$/);
  await confirmSolo(page);
  const introduction = await page
    .locator(".round-intro")
    .evaluate((element) => ({
      text: element.textContent ?? "",
      endpointCategory:
        element.querySelector(".round-intro__endpoint-category")?.textContent ??
        "",
      mode: element.querySelector(".round-intro__mode")?.textContent ?? "",
      registration:
        element.querySelector(".round-intro__registration")?.textContent ?? "",
    }));
  expect(introduction.text).toContain("Art & Design");
  expect(introduction.text).toContain("Hokusai");
  expect(introduction.text).toContain("United Kingdom");
  expect(introduction.endpointCategory.trim()).toBe(
    "Atlas category Art & Design",
  );
  expect(introduction.mode.trim()).toBe("Solo route");
  expect(introduction.registration).not.toContain("WW /");
  expect(introduction.registration).not.toContain("SEC");
  await expect(page.locator(".round-intro")).toBeHidden({ timeout: 20_000 });
  const round = page.getByRole("region", { name: "Reach United Kingdom" });
  await expect(round).toBeVisible();
  await expect(round.locator(".round-masthead__state-full")).toHaveText(
    "Round active",
  );
  await expect(round.locator(".round-masthead__timer-context")).toHaveText(
    "Timer running",
  );
  await expect(round).toContainText("Solo route");
  await expect(round).toContainText("Normal difficulty");
  const phoneLayout = (page.viewportSize()?.width ?? 0) <= 512;
  if (phoneLayout) {
    await expect(round.getByText("Score", { exact: true })).toBeHidden();
  } else {
    await expect(round.getByText("Score", { exact: true })).toBeVisible();
  }
  await expect(round.locator("dl.game-metrics")).toHaveAttribute(
    "aria-live",
    "off",
  );
  await expect(page.locator(".game-map")).toBeVisible();
  const mapHelp = page.getByRole("button", { name: "Map controls help" });
  if (phoneLayout) {
    await expect(mapHelp).toBeHidden();
  } else {
    await expect(mapHelp).toBeVisible();
  }
  await expect(page.locator(".map-viewport__instructions")).toHaveCSS(
    "clip-path",
    "inset(50%)",
  );
  if (!phoneLayout) {
    await mapHelp.click();
    await expect(
      page.getByRole("note", { name: "Map controls" }),
    ).toBeVisible();
    await mapHelp.click();
  }
  const mapViewport = page.locator(".game-map__viewport");
  const initialMapSize = await page
    .locator(".map-viewport__world")
    .evaluate((element) => ({
      width: (element as HTMLElement).offsetWidth,
      height: (element as HTMLElement).offsetHeight,
    }));
  await expect(page.locator(".map-board-renderer")).toHaveAttribute(
    "data-render-state",
    /ready|fallback/,
  );
  const movePrompt = page.getByRole("heading", {
    name: "Where do you go next?",
  });
  if (phoneLayout) {
    await expect(movePrompt).toBeHidden();
  } else {
    await expect(movePrompt).toBeVisible();
  }
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
      name: /(?:Move to|Preview route to) The Great Wave off Kanagawa: The Great Wave off Kanagawa is a notable work by Hokusai\./i,
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
  const compassPrompt = page.getByRole("heading", {
    name: "Which route should the Compass check?",
  });
  if (phoneLayout) {
    await expect(compassPrompt).toBeHidden();
    await expect(
      page.getByRole("button", {
        name: /Compass hint.*choose a route to evaluate/i,
      }),
    ).toHaveAttribute("aria-pressed", "true");
  } else {
    await expect(compassPrompt).toBeVisible();
  }
  await activateMapChoice(
    page,
    page
      .locator("button.map-choice")
      .filter({ hasText: "The Great Wave off Kanagawa" }),
  );
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
  const hintMessageBounds = await page
    .locator(".hint-dock__message")
    .boundingBox();
  const mapViewportBounds = await page.locator(".map-viewport").boundingBox();
  expect(hintMessageBounds).not.toBeNull();
  expect(mapViewportBounds).not.toBeNull();
  if (page.viewportSize()!.width > 800) {
    expect(hintMessageBounds!.x).toBeGreaterThanOrEqual(
      mapViewportBounds!.x + mapViewportBounds!.width,
    );
  } else {
    expect(hintMessageBounds!.y).toBeGreaterThanOrEqual(
      mapViewportBounds!.y + mapViewportBounds!.height,
    );
  }
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
  const expandedMapSize = await page
    .locator(".map-viewport__world")
    .evaluate((element) => ({
      width: (element as HTMLElement).offsetWidth,
      height: (element as HTMLElement).offsetHeight,
    }));
  if ((await mapViewport.getAttribute("data-map-layout")) === "vertical") {
    expect(expandedMapSize.width).toBe(initialMapSize.width);
    expect(expandedMapSize.height).toBeGreaterThan(initialMapSize.height);
  } else {
    expect(expandedMapSize.width).toBeGreaterThan(initialMapSize.width);
  }
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

  await expect(
    page.getByRole("button", { name: /In-game Back/i }),
  ).toBeEnabled();
  const quickBackTarget = page.locator('[data-map-back-target="true"]');
  await expect(quickBackTarget).toHaveCount(1);
  await expect(quickBackTarget).toHaveAttribute(
    "aria-label",
    "Preview Back to Hokusai",
  );
  await quickBackTarget.click();
  await expect(quickBackTarget).toHaveAttribute("aria-pressed", "true");
  await expect(quickBackTarget).toHaveAttribute(
    "aria-label",
    "Back to Hokusai",
  );
  await expect(
    quickBackTarget.locator(".map-history-node__back-confirm"),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: "The Great Wave off Kanagawa",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".game-map__trail li")).toHaveCount(2);
  await quickBackTarget.click();
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".game-map__trail li")).toHaveCount(3);
  await expect(
    page.locator(".map-history-node--discarded").filter({
      hasText: "The Great Wave off Kanagawa",
    }),
  ).toBeVisible();
  const retracedMapSize = await page
    .locator(".map-viewport__world")
    .evaluate((element) => ({
      width: (element as HTMLElement).offsetWidth,
      height: (element as HTMLElement).offsetHeight,
    }));
  if ((await mapViewport.getAttribute("data-map-layout")) === "vertical") {
    expect(retracedMapSize.width).toBe(expandedMapSize.width);
    expect(retracedMapSize.height).toBeGreaterThan(expandedMapSize.height);
  } else {
    expect(retracedMapSize.width).toBeGreaterThan(expandedMapSize.width);
  }
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
  await activateMapChoice(page, series);
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
    page.getByRole("region", { name: "This branch ends here" }),
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
  await expect(
    page.locator(".map-position--current").filter({ hasText: "Hokusai" }),
  ).toBeVisible();
  if ((page.viewportSize()?.width ?? Number.POSITIVE_INFINITY) <= 512) {
    await expect
      .poll(async () => {
        const [viewportBounds, currentBounds] = await Promise.all([
          page.locator(".game-map__viewport").boundingBox(),
          page
            .locator(".map-position--current")
            .filter({ hasText: "Hokusai" })
            .boundingBox(),
        ]);
        return Boolean(
          viewportBounds &&
            currentBounds &&
            currentBounds.y >= viewportBounds.y - 1 &&
            currentBounds.y + currentBounds.height <=
              viewportBounds.y + viewportBounds.height + 1,
        );
      })
      .toBe(true);
  } else {
    await expect
      .poll(() =>
        mapWorld.evaluate((element) => getComputedStyle(element).transform),
      )
      .toBe(cameraBeforeRecovery);
  }
  await expect(page.locator(".game-map__dead-end")).toHaveCount(0);
});

test("Hard selection reveals its category and endpoints before controls unlock", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/play/solo");
  await confirmSolo(page, "Hard");
  await expect(page.locator(".game-page__play")).toHaveAttribute("inert", "");
  const introduction = page.locator(".round-intro");
  const artworks = introduction.locator(
    ".round-intro__artwork.endpoint-artwork--fit-contain",
  );
  const artworkImages = artworks.locator(".endpoint-artwork__image");
  await expect(introduction).toContainText("Hokusai");
  await expect(introduction).toContainText("England");
  await expect(artworks).toHaveCount(2);
  await expect(artworks.locator(".endpoint-artwork__backdrop")).toHaveCount(2);
  await expect(artworkImages).toHaveCount(2);
  await expect(artworkImages.first()).toHaveCSS("object-fit", "contain");
  await expect(artworkImages.nth(1)).toHaveCSS("object-fit", "contain");
  await expect(page.locator(".round-intro")).toBeHidden({ timeout: 20_000 });
  await expect(page.locator(".game-page__play")).not.toHaveAttribute(
    "inert",
    "",
  );
});

test("Daily and Multiplayer expose their complete entry states", async ({
  page,
}) => {
  test.setTimeout(60_000);
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
  await expect(page.locator(".round-intro")).toBeHidden({ timeout: 20_000 });
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Daily connection",
  );

  await page.goto("/lobby");
  await page.getByRole("button", { name: /Create lobby/i }).click();
  await expect(page.getByText("MAPS27", { exact: true })).toBeVisible();
  await expect(page.getByText("2 / 4", { exact: true })).toBeVisible();
  await expect(page.locator(".room-route-stamp")).toContainText(
    "Art & Design · Normal",
  );
  await page.getByRole("button", { name: "I’m ready" }).click();
  await page.getByRole("button", { name: /Start game/i }).click();
  await expect(page).toHaveURL(/\/lobby\/MAPS27$/);
  const relayIntroduction = page.locator(".round-intro");
  if (await relayIntroduction.isVisible()) {
    await expect(page.locator(".round-intro__mode")).toHaveText("Multiplayer");
    await expect(relayIntroduction).toBeHidden({ timeout: 20_000 });
  }
  await expect(page.locator(".round-masthead__meta")).toContainText(
    "Multiplayer",
  );

  for (const entity of [
    "The Great Wave off Kanagawa",
    "British Museum",
    "London",
    "United Kingdom",
  ]) {
    await followTo(page, entity);
  }
  await expect(page).toHaveURL(/\/lobby\/MAPS27\/results$/);
  await expect(page.locator(".route-confetti")).toHaveCount(1);
  await expect(page.locator(".result-hero__copy")).toContainText(
    "Multiplayer round complete",
  );
  await expect(
    page.getByRole("heading", { name: "Race another round?" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Yes, race again" }),
  ).toBeVisible();
});

test("a lobby invite deep link confirms before reusing the current window", async ({
  page,
}) => {
  await page.goto("/lobby");
  const prompt = page.getByRole("dialog", {
    name: "What should other explorers call you?",
  });
  await prompt.getByRole("button", { name: "Continue", exact: true }).click();
  await page.getByRole("button", { name: /Create lobby/i }).click();
  await expect(
    page.getByRole("button", { name: "Share lobby MAPS27" }),
  ).toBeVisible();

  await page.evaluate(() => {
    window.history.pushState({}, "", "/lobby/MAPS27/join");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  const invitation = page.getByRole("dialog", { name: /invited you/i });
  await expect(invitation).toContainText("Open it in this Webwoven window?");
  await invitation.getByRole("button", { name: "Open lobby" }).click();

  await expect(page).toHaveURL(/\/lobby$/);
  await expect(page.getByText("MAPS27", { exact: true })).toBeVisible();
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
  await expect(page.locator(".round-intro")).toBeHidden({ timeout: 20_000 });

  for (const entity of [
    "The Great Wave off Kanagawa",
    "British Museum",
    "London",
    "United Kingdom",
  ]) {
    await followTo(page, entity);
  }

  await expect(page).toHaveURL(/\/results$/);
  await expect(page.locator(".route-confetti")).toHaveCount(1);
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

test("Settings edits the public name and locks it during Multiplayer", async ({
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
  await page.getByRole("button", { name: /Create lobby/i }).click();
  await page.getByRole("button", { name: /Open settings/i }).click();
  await expect(page.getByLabel("Public explorer name")).toBeDisabled();
  await expect(
    page.getByText(/name is locked during a multiplayer round/i),
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
  await expect(page.locator(".round-intro")).toBeHidden({ timeout: 20_000 });

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
