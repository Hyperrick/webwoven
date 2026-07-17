import { expect, test } from "@playwright/test";
import { followTo, startSolo } from "./helpers";

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
  await expect(page.locator(".result-hero__copy")).toContainText(
    "Solo route complete",
  );
  const routeArtwork = page.locator(
    ".route-reveal__artwork.endpoint-artwork--fit-contain",
  );
  await expect(routeArtwork).toHaveCount(5);
  await expect(routeArtwork.locator(".endpoint-artwork__backdrop")).toHaveCount(
    5,
  );
  await expect(
    routeArtwork.first().locator(".endpoint-artwork__image"),
  ).toHaveCSS("object-fit", "contain");
  if ((page.viewportSize()?.width ?? Number.POSITIVE_INFINITY) <= 800) {
    const routeStepHeights = await page
      .locator(".route-reveal li")
      .evaluateAll((steps) =>
        steps.map((step) => (step as HTMLElement).offsetHeight),
      );
    expect(Math.max(...routeStepHeights)).toBeLessThan(120);
  }
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
