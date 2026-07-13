import { expect, test, type Page } from "@playwright/test";

async function followTo(page: Page, entity: string): Promise<void> {
  const toggles = page.locator("button.relation-group__toggle");
  for (let index = 0; index < (await toggles.count()); index += 1) {
    const toggle = toggles.nth(index);
    if ((await toggle.getAttribute("aria-expanded")) !== "true")
      await toggle.click();
    const candidate = page.getByRole("button", {
      name: new RegExp(entity, "i"),
    });
    if (await candidate.isVisible()) {
      await candidate.click();
      await expect(
        page
          .locator(".entity-stage h1, .result-hero h1")
          .filter({ hasText: entity })
          .first(),
      ).toBeVisible();
      return;
    }
  }
  throw new Error(`No playable relation leads to ${entity}`);
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
  await expect(
    page.getByRole("heading", { name: "Hokusai", exact: true }),
  ).toBeVisible();

  await followTo(page, "The Great Wave off Kanagawa");
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
  await expect(page.getByText("02", { exact: true }).first()).toBeVisible();
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
});

test("Daily and Live Relay expose their complete entry states", async ({
  page,
}) => {
  await page.goto("/play/daily");
  await expect(
    page.getByText("Daily connection", { exact: true }),
  ).toBeVisible();

  await page.goto("/relay");
  await page.getByRole("button", { name: /Create relay/i }).click();
  await expect(page.getByText("MAPS27", { exact: true })).toBeVisible();
  await expect(page.getByText("2 / 4", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "I’m ready" }).click();
  await page.getByRole("button", { name: /Start relay/i }).click();
  await expect(page).toHaveURL(/\/relay\/MAPS27$/);
  await expect(page.getByText("Live relay", { exact: true })).toBeVisible();
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
