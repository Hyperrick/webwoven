import { expect, test } from "@playwright/test";

test("landing communicates the game and its three play modes", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "The shortest route is rarely a straight line.",
  );
  const chooser = page.getByRole("region", { name: "Select play mode" });
  const modes = [
    {
      name: /Single player/i,
      copy: "Find a route at your own pace.",
      path: /\/play\/solo$/,
    },
    {
      name: /Daily challenge/i,
      copy: "Solve the same route as everyone today.",
      path: /\/play\/daily$/,
    },
    {
      name: /Multiplayer/i,
      copy: "Race live with 2–4 players.",
      path: /\/relay$/,
    },
  ];

  await expect(chooser).toBeVisible();
  await expect(chooser.getByRole("button")).toHaveCount(3);
  for (const mode of modes) {
    const button = chooser.getByRole("button", { name: mode.name });
    await expect(button).toBeInViewport({ ratio: 1 });
    await expect(button.getByText(mode.copy, { exact: true })).toBeVisible();
  }
  const routePreview = page.getByLabel("Example knowledge route");
  await expect(routePreview.locator(".landing-route-map")).toBeVisible();
  await expect(routePreview.locator(".landing-route-map__drawing")).toBeVisible();
  await expect(routePreview.locator("li")).toHaveCount(5);
  await expect(routePreview.locator(".hero-route__step--hidden")).toHaveCount(
    3,
  );
  await expect(
    routePreview.locator(".hero-route__step--hidden strong"),
  ).toHaveText(["…", "…", "…"]);
  await expect(page.getByText("Build Week", { exact: false })).toHaveCount(0);

  for (const mode of modes) {
    await page.goto("/");
    await page
      .getByRole("region", { name: "Select play mode" })
      .getByRole("button", { name: mode.name })
      .click();
    await expect(page).toHaveURL(mode.path);
  }

  const relayPrompt = page.getByRole("dialog", {
    name: "What should other explorers call you?",
  });
  await expect(relayPrompt).toContainText("Live relay");
  await expect(relayPrompt).toContainText("room roster and live race");
});
