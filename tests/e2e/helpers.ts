import { expect, type Page } from "@playwright/test";

export async function confirmSolo(
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

export async function startSolo(
  page: Page,
  difficulty: "Easy" | "Normal" | "Hard" = "Normal",
): Promise<void> {
  await page.goto("/play/solo");
  await confirmSolo(page, difficulty);
  await expect(page.locator(".round-intro")).toHaveCount(0, {
    timeout: 10_000,
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
  await candidate.click();
  await expect(
    page
      .locator(".map-position--current h3, .result-hero h1")
      .filter({ hasText: entity })
      .first(),
  ).toBeVisible();
}
