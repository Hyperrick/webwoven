<script lang="ts">
  import type { HintType, RelationGroup, UsedHint } from "../api/types";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    groups,
    used,
    disabled = false,
    compassSelecting = false,
    onHint,
    onCompassToggle,
  }: {
    groups: RelationGroup[];
    used: UsedHint[];
    disabled?: boolean;
    compassSelecting?: boolean;
    onHint: (type: HintType, propertyId?: string) => void;
    onCompassToggle: () => void;
  } = $props();

  const tools = [
    { type: "compass", label: "Compass", penalty: 75, icon: "compass" },
    { type: "lens", label: "Lens", penalty: 150, icon: "lens" },
    {
      type: "map_fragment",
      label: "Map fragment",
      penalty: 250,
      icon: "map",
    },
  ] as const;

  const hintUsed = (type: HintType) => used.some((hint) => hint.type === type);
  let latest = $derived(used.at(-1));
  let remaining = $derived(tools.length - used.length);
  let noRoutes = $derived(groups.length === 0);
</script>

<aside class="hint-dock" aria-labelledby="hint-title">
  <div class="hint-dock__heading">
    <h2 id="hint-title">Hint tools</h2>
    <p>{remaining} ready</p>
  </div>
  <div class="hint-dock__actions" role="group" aria-label="One-use hints">
    {#each tools as tool, index}
      {@const isUsed = hintUsed(tool.type)}
      <button
        type="button"
        class:hint-dock__tool--used={isUsed}
        aria-label={`${tool.label} hint, ${tool.penalty} point penalty, ${isUsed ? "used" : tool.type === "compass" && compassSelecting ? "choose a route to evaluate" : "ready"}`}
        aria-pressed={tool.type === "compass" ? compassSelecting : undefined}
        disabled={disabled || isUsed || noRoutes}
        onclick={() => {
          if (tool.type === "compass") onCompassToggle();
          else onHint(tool.type);
        }}
      >
        <span class="hint-dock__slot" aria-hidden="true">{index + 1}</span>
        <AtlasIcon name={tool.icon} size={20} />
        <span class="hint-dock__tool-copy">
          <strong>{tool.label}</strong>
          <small>−{tool.penalty} pts</small>
        </span>
        <span class="hint-dock__tool-state" aria-hidden="true">
          {isUsed
            ? "Used"
            : noRoutes
              ? "Unavailable"
              : tool.type === "compass" && compassSelecting
                ? "Choosing"
                : "Ready"}
        </span>
      </button>
    {/each}
  </div>
  {#if latest}
    <p
      class="hint-dock__message"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <strong>Latest hint</strong>
      <span>{latest.message}</span>
    </p>
  {/if}
</aside>
