import { expect, test } from "@playwright/test";

import { startSolo } from "./helpers";

const LONG_PRODUCTION_LABEL =
  "doctor honoris causa from the University of Lyon";

for (const viewport of [
  { width: 320, height: 568 },
  { width: 390, height: 844 },
]) {
  test(`mobile choice rows fit their tallest full label at ${viewport.width}x${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await startSolo(page);

    const mapViewport = page.locator(".game-map__viewport");
    await expect(mapViewport).toHaveAttribute(
      "data-map-presentation",
      "constellation",
    );

    const choice = page.locator("[data-mobile-choice-node]").first();
    const labelFrame = choice.locator(".mobile-map-choice-node__label");
    const labelText = labelFrame.locator(".mobile-map-choice-node__label-text");
    await labelText.evaluate((element, label) => {
      element.textContent = label;
    }, LONG_PRODUCTION_LABEL);
    await page
      .locator("[data-mobile-choice-node]")
      .nth(1)
      .locator(".mobile-map-choice-node__label-text")
      .evaluate((element) => {
        element.textContent = "Short";
      });

    await expect
      .poll(async () =>
        Number(await choice.getAttribute("data-mobile-label-lines")),
      )
      .toBeGreaterThanOrEqual(3);

    await page.locator(".map-viewport__world").evaluate((world) => {
      const templates = [
        ...world.querySelectorAll<HTMLElement>("[data-mobile-choice-node]"),
      ].slice(0, 2);
      if (templates.length !== 2)
        throw new Error("Two mobile row templates are required");
      const firstRowTop = Number.parseFloat(getComputedStyle(templates[0]).top);
      const rootSize = Number.parseFloat(
        getComputedStyle(document.documentElement).fontSize,
      );
      templates.forEach((template, index) => {
        const fixture = template.cloneNode(true) as HTMLElement;
        fixture.dataset.mobileRowFixture = "true";
        fixture.dataset.mapNodeId = `row-fixture-${index}`;
        fixture.dataset.mobileLabelLines = "2";
        fixture.removeAttribute("data-map-near-focus");
        fixture.setAttribute("aria-hidden", "true");
        fixture.setAttribute("inert", "");
        fixture.style.setProperty("--mobile-choice-label-lines", "2");
        fixture.style.top = `${firstRowTop + 7.4 * rootSize}px`;
        const fixtureText = fixture.querySelector<HTMLElement>(
          ".mobile-map-choice-node__label-text",
        );
        if (!fixtureText) throw new Error("Row fixture label is missing");
        fixtureText.textContent = `Fixture ${index + 1}`;
        world.append(fixture);
      });
    });
    await expect(page.locator("[data-mobile-row-fixture]")).toHaveCount(2);

    const geometry = await labelFrame.evaluate((frame) => {
      const text = frame.querySelector<HTMLElement>(
        ".mobile-map-choice-node__label-text",
      );
      const node = frame.closest<HTMLElement>("[data-mobile-choice-node]");
      const viewportElement = frame.closest<HTMLElement>(".game-map__viewport");
      if (!text || !node || !viewportElement)
        throw new Error("Mobile label fixture is incomplete");

      const frameBounds = frame.getBoundingClientRect();
      const nodeBounds = node.getBoundingClientRect();
      const viewportBounds = viewportElement.getBoundingClientRect();
      const choiceBounds = [
        ...viewportElement.querySelectorAll<HTMLElement>(
          "[data-mobile-choice-node]",
        ),
      ].map((choiceNode) => choiceNode.getBoundingClientRect());
      const firstRowNodes = [
        ...node.parentElement!.querySelectorAll<HTMLElement>(
          "[data-mobile-choice-node]",
        ),
      ].slice(0, 2);
      const nextRowNodes = [
        ...viewportElement.querySelectorAll<HTMLElement>(
          "[data-mobile-row-fixture]",
        ),
      ];
      const shortFrame = firstRowNodes[1]?.querySelector<HTMLElement>(
        ".mobile-map-choice-node__label",
      );
      const shortText = shortFrame?.querySelector<HTMLElement>(
        ".mobile-map-choice-node__label-text",
      );
      const frameStyle = getComputedStyle(frame);
      const textStyle = getComputedStyle(text);
      const textBounds = text.getBoundingClientRect();
      const range = document.createRange();
      range.selectNodeContents(text);
      const lineBounds = [...range.getClientRects()].map((bounds) => ({
        top: bounds.top,
        bottom: bounds.bottom,
      }));
      const visibleLineTops = lineBounds.reduce<number[]>((tops, line) => {
        if (!tops.some((top) => Math.abs(top - line.top) <= 1)) {
          tops.push(line.top);
        }
        return tops;
      }, []);

      return {
        frameInsideNode:
          frameBounds.left >= nodeBounds.left - 1 &&
          frameBounds.right <= nodeBounds.right + 1 &&
          frameBounds.bottom <= nodeBounds.bottom + 1,
        frameInsideViewport:
          frameBounds.left >= viewportBounds.left - 1 &&
          frameBounds.right <= viewportBounds.right + 1 &&
          frameBounds.top >= viewportBounds.top - 1 &&
          frameBounds.bottom <= viewportBounds.bottom + 1,
        textInsideFrame:
          textBounds.top >= frameBounds.top - 1 &&
          textBounds.bottom <= frameBounds.bottom + 1,
        visibleLineCount: visibleLineTops.length,
        completeText: text.textContent,
        textFits: text.scrollHeight <= text.clientHeight + 1,
        rowLabelLines: Number.parseInt(
          node.dataset.mobileLabelLines ?? "0",
          10,
        ),
        firstRowFrameHeights: [
          ...node.parentElement!.querySelectorAll<HTMLElement>(
            "[data-mobile-choice-node] .mobile-map-choice-node__label",
          ),
        ]
          .slice(0, 2)
          .map((label) => label.getBoundingClientRect().height),
        shortTextCenterOffset:
          shortFrame && shortText
            ? Math.abs(
                (shortFrame.getBoundingClientRect().top +
                  shortFrame.getBoundingClientRect().bottom) /
                  2 -
                  (shortText.getBoundingClientRect().top +
                    shortText.getBoundingClientRect().bottom) /
                    2,
              )
            : Number.POSITIVE_INFINITY,
        nextRowClearance:
          Math.min(
            ...nextRowNodes.map(
              (choiceNode) => choiceNode.getBoundingClientRect().top,
            ),
          ) -
          Math.max(
            ...firstRowNodes.map(
              (choiceNode) => choiceNode.getBoundingClientRect().bottom,
            ),
          ),
        choicesOverlap: choiceBounds.some((left, leftIndex) =>
          choiceBounds
            .slice(leftIndex + 1)
            .some(
              (right) =>
                left.left < right.right - 1 &&
                left.right > right.left + 1 &&
                left.top < right.bottom - 1 &&
                left.bottom > right.top + 1,
            ),
        ),
        frameHeight: frameBounds.height,
        frameOverflow: frameStyle.overflow,
        textOverflow: textStyle.overflow,
        textOverflowMode: textStyle.textOverflow,
        lineClamp: textStyle.webkitLineClamp,
        documentWidth: document.documentElement.clientWidth,
        documentScrollWidth: document.documentElement.scrollWidth,
      };
    });

    expect(geometry.frameInsideNode).toBe(true);
    expect(geometry.frameInsideViewport).toBe(true);
    expect(geometry.textInsideFrame).toBe(true);
    expect(geometry.visibleLineCount).toBeGreaterThanOrEqual(3);
    expect(geometry.completeText).toBe(LONG_PRODUCTION_LABEL);
    expect(geometry.textFits).toBe(true);
    expect(geometry.rowLabelLines).toBe(geometry.visibleLineCount);
    expect(geometry.firstRowFrameHeights).toHaveLength(2);
    expect(geometry.firstRowFrameHeights[0]).toBeCloseTo(
      geometry.frameHeight,
      1,
    );
    expect(geometry.firstRowFrameHeights[1]).toBeCloseTo(
      geometry.frameHeight,
      1,
    );
    expect(geometry.shortTextCenterOffset).toBeLessThanOrEqual(1);
    expect(geometry.nextRowClearance).toBeGreaterThanOrEqual(-1);
    expect(geometry.choicesOverlap).toBe(false);
    expect(geometry.frameOverflow).toBe("visible");
    expect(geometry.textOverflow).toBe("visible");
    expect(geometry.textOverflowMode).toBe("clip");
    expect(geometry.lineClamp).toBe("none");
    expect(geometry.documentScrollWidth).toBeLessThanOrEqual(
      geometry.documentWidth,
    );
  });
}

test("a confirmed mobile move reveals the complete new frontier", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await startSolo(page);

  const currentNode = page.locator("[data-map-current]:not([inert])");
  const initialCurrentNodeId =
    await currentNode.getAttribute("data-map-node-id");
  const firstChoice = page.locator("[data-mobile-choice-node]").first();
  await firstChoice.click();
  await expect(firstChoice).toHaveAttribute("aria-pressed", "true");

  await page.locator(".map-viewport__world").evaluate((world) => {
    const template = world.querySelector<HTMLElement>(
      "[data-mobile-choice-node]",
    );
    if (!template) throw new Error("Mobile choice fixture is missing");
    for (let index = 0; index < 4; index += 1) {
      const fixture = template.cloneNode(true) as HTMLElement;
      fixture.dataset.mobileChoiceFixture = "true";
      fixture.dataset.mapNodeId = `fixture-choice-${index}`;
      fixture.removeAttribute("data-map-near-focus");
      fixture.setAttribute("aria-hidden", "true");
      fixture.setAttribute("inert", "");
      fixture.style.setProperty("--node-x", index % 2 === 0 ? "27%" : "73%");
      fixture.style.setProperty("--node-y", index < 2 ? "72%" : "86%");
      world.append(fixture);
    }
  });
  await expect(page.locator("[data-mobile-choice-fixture]")).toHaveCount(4);
  await expect(page.locator("[data-mobile-choice-node]")).toHaveCount(6);

  await firstChoice.click();
  await expect(currentNode).not.toHaveAttribute(
    "data-map-node-id",
    initialCurrentNodeId ?? "",
  );

  await expect
    .poll(async () => {
      const viewportBounds = await page
        .locator(".game-map__viewport")
        .boundingBox();
      const frontierBounds = await page
        .locator("[data-mobile-choice-node]")
        .evaluateAll((elements) =>
          elements.map((element) => {
            const bounds = element.getBoundingClientRect();
            return {
              left: bounds.left,
              top: bounds.top,
              right: bounds.right,
              bottom: bounds.bottom,
            };
          }),
        );
      if (!viewportBounds || frontierBounds.length === 0) return false;
      if (frontierBounds.length < 6) return false;
      return frontierBounds.every(
        ({ left, top, right, bottom }) =>
          left >= viewportBounds.x - 1 &&
          right <= viewportBounds.x + viewportBounds.width + 1 &&
          top >= viewportBounds.y - 1 &&
          bottom <= viewportBounds.y + viewportBounds.height + 1,
      );
    })
    .toBe(true);
});
