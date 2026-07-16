import { expect, test } from "@playwright/test";
import { startSolo } from "./helpers";

test("the inspector anchors locally and recovers the retained map canvas", async ({
  page,
}) => {
  await startSolo(page);
  const renderer = page.locator(".map-board-renderer");
  await expect(renderer).toHaveAttribute("data-render-state", /ready|fallback/);

  const currentCard = page.locator(".map-position--current");
  await page
    .getByRole("button", { name: "Inspect current entity: Hokusai" })
    .click();
  const inspector = page.getByRole("dialog", { name: "Hokusai" });
  await expect(inspector).toBeVisible();
  await expect(
    inspector.getByText("How it connects", { exact: true }),
  ).toHaveCount(0);

  if ((page.viewportSize()?.width ?? 0) > 800) {
    const [currentBounds, inspectorBounds] = await Promise.all([
      currentCard.boundingBox(),
      inspector.boundingBox(),
    ]);
    expect(currentBounds).not.toBeNull();
    expect(inspectorBounds).not.toBeNull();
    expect(inspectorBounds!.x).toBeGreaterThan(
      currentBounds!.x + currentBounds!.width,
    );
    expect(
      inspectorBounds!.x - (currentBounds!.x + currentBounds!.width),
    ).toBeLessThanOrEqual(16);
  }

  if ((await renderer.getAttribute("data-render-state")) === "ready") {
    const canvas = renderer.locator("canvas");
    await expect
      .poll(() =>
        canvas.evaluate((element) => {
          const context = (element as HTMLCanvasElement).getContext("webgl2");
          return context?.getContextAttributes()?.preserveDrawingBuffer;
        }),
      )
      .toBe(true);

    await canvas.evaluate(async (element) => {
      const context = (element as HTMLCanvasElement).getContext("webgl2");
      if (!context) return;
      window.dispatchEvent(new Event("focus"));
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => {
          context.clearColor(0, 0, 0, 0);
          context.clear(context.COLOR_BUFFER_BIT);
          resolve();
        });
      });
    });

    await expect
      .poll(() =>
        canvas.evaluate((element) => {
          const canvasElement = element as HTMLCanvasElement;
          const context = canvasElement.getContext("webgl2");
          if (!context) return 0;
          const pixel = new Uint8Array(4);
          context.readPixels(
            Math.floor(canvasElement.width / 2),
            Math.floor(canvasElement.height / 2),
            1,
            1,
            context.RGBA,
            context.UNSIGNED_BYTE,
            pixel,
          );
          return pixel[3];
        }),
      )
      .toBeGreaterThan(0);
  }
});
