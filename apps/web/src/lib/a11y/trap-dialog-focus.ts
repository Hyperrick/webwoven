import type { Action } from "svelte/action";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

function focusableElements(node: HTMLElement): HTMLElement[] {
  return [...node.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)].filter(
    (element) => element.getClientRects().length > 0,
  );
}

export const trapDialogFocus: Action<HTMLElement> = (node) => {
  function keepFocusInside(event: KeyboardEvent): void {
    if (event.key !== "Tab") return;

    const focusable = focusableElements(node);
    if (focusable.length === 0) {
      event.preventDefault();
      node.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable.at(-1)!;
    const active = document.activeElement;
    const movingBeforeFirst = event.shiftKey && active === first;
    const movingPastLast = !event.shiftKey && active === last;
    const focusEscaped = !node.contains(active);

    if (!movingBeforeFirst && !movingPastLast && !focusEscaped) return;

    event.preventDefault();
    (event.shiftKey ? last : first).focus();
  }

  node.addEventListener("keydown", keepFocusInside);
  return {
    destroy: () => node.removeEventListener("keydown", keepFocusInside),
  };
};
