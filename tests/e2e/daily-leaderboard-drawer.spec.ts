import { expect, test } from "@playwright/test";
import { followTo, startSolo } from "./helpers";

test("Daily leaderboard opens without interrupting an active Solo round", async ({
  page,
}) => {
  await startSolo(page);
  await followTo(page, "The Great Wave off Kanagawa");

  const trigger = page.getByRole("button", {
    name: "Open Daily leaderboard",
  });
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await trigger.click();

  const drawer = page.getByRole("dialog", { name: "Today’s field" });
  const close = drawer.getByRole("button", {
    name: "Close Daily leaderboard",
  });
  await expect(drawer).toBeVisible();
  await expect(drawer.locator(".eyebrow")).toHaveText("Daily leaderboard");
  await expect(drawer).toHaveAttribute("aria-modal", "true");
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await expect(close).toBeFocused();
  await expect(page.locator("#page-content")).toHaveAttribute("inert", "");
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(close).toBeFocused();
  await expect(page).toHaveURL(/\/play\/solo$/);
  await expect(
    page.getByRole("alertdialog", { name: /Your map is still unfinished/i }),
  ).toHaveCount(0);
  await expect(drawer.getByText("PaperFox", { exact: true })).toBeVisible();
  await expect(drawer.getByText("Northstar", { exact: true })).toBeVisible();
  await expect(drawer.getByText("Mira", { exact: true })).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await expect(trigger).toBeFocused();
  await expect(page).toHaveURL(/\/play\/solo$/);
  await expect(
    page
      .locator(".map-position--current h3")
      .filter({ hasText: "The Great Wave off Kanagawa" }),
  ).toBeVisible();
  await expect(
    page
      .locator(".game-metrics div")
      .filter({ hasText: "Moves" })
      .locator("dd"),
  ).toHaveText("1");

  await trigger.click();
  await close.click();
  await expect(trigger).toBeFocused();
});
