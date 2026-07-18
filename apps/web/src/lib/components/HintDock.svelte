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
    onHint: (type: HintType, propertyId?: string, entityQid?: string) => void;
    onCompassToggle: () => void;
  } = $props();

  const tools = [
    {
      type: "compass",
      label: "Compass",
      help: "Check one route: promising, longer, or a dead end.",
      penalty: 75,
      icon: "compass",
    },
    {
      type: "lens",
      label: "Lens",
      help: "Reveal one near-optimal next move.",
      penalty: 150,
      icon: "lens",
    },
    {
      type: "map_fragment",
      label: "Map fragment",
      help: "Reveal one valid bridge toward the goal.",
      penalty: 250,
      icon: "map",
    },
  ] as const;

  const hintUsed = (type: HintType) => used.some((hint) => hint.type === type);
  let latest = $derived(used.at(-1));
  let noRoutes = $derived(groups.length === 0);
</script>

<aside
  class="hint-dock"
  class:hint-dock--has-message={Boolean(latest)}
  aria-labelledby="hint-title"
>
  <div class="hint-dock__heading">
    <h2 id="hint-title">Hint tools</h2>
  </div>
  <div class="hint-dock__actions" role="group" aria-label="One-use hints">
    {#each tools as tool}
      {@const isUsed = hintUsed(tool.type)}
      {@const helpId = `hint-tool-${tool.type}-help`}
      <div class="hint-dock__tool">
        <button
          type="button"
          class:hint-dock__tool--used={isUsed}
          aria-label={`${tool.label} hint. ${tool.penalty} point penalty. ${isUsed ? "Used" : tool.type === "compass" && compassSelecting ? "Choose a route to evaluate" : "Ready"}.`}
          aria-describedby={helpId}
          aria-pressed={tool.type === "compass" ? compassSelecting : undefined}
          disabled={disabled || isUsed || noRoutes}
          onclick={() => {
            if (tool.type === "compass") onCompassToggle();
            else onHint(tool.type);
          }}
        >
          <AtlasIcon name={tool.icon} size={22} />
          <span class="hint-dock__tool-copy">
            <strong>{tool.label}</strong>
            <small class="hint-dock__tool-penalty">
              <span class="hint-dock__tool-penalty-full"
                >−{tool.penalty} pts</span
              >
              <span class="hint-dock__tool-penalty-compact" aria-hidden="true"
                >−{tool.penalty}</span
              >
            </small>
          </span>
          <span class="hint-dock__tool-state" aria-hidden="true">
            {isUsed
              ? "Used"
              : noRoutes
                ? "Unavailable"
                : tool.type === "compass" && compassSelecting
                  ? "Choosing"
                  : ""}
          </span>
        </button>
        <small class="hint-dock__tool-help" id={helpId} role="tooltip">
          {tool.help}
        </small>
      </div>
    {/each}
  </div>
  {#if latest}
    <p
      class="hint-dock__message"
      role="status"
      aria-live="polite"
      aria-atomic="true"
      title={latest.message}
    >
      <strong>Latest hint</strong>
      <span>{latest.message}</span>
    </p>
  {/if}
</aside>
