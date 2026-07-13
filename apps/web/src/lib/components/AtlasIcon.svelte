<script lang="ts">
  import type { RelationGroup } from "../api/types";

  type IconName =
    | RelationGroup["glyph"]
    | "arrow"
    | "back"
    | "check"
    | "close"
    | "compass"
    | "lens"
    | "map"
    | "menu"
    | "route"
    | "settings"
    | "sources"
    | "users";

  let { name, size = 20 }: { name: IconName; size?: number } = $props();
</script>

<svg
  class="atlas-icon"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill="none"
  aria-hidden="true"
>
  {#if name === "arrow"}
    <path d="M5 12h13m-5-5 5 5-5 5" />
  {:else if name === "back"}
    <path d="m10 6-6 6 6 6M4 12h11a5 5 0 0 1 5 5" />
  {:else if name === "check"}
    <path d="m5 12 4 4L19 6" />
  {:else if name === "close"}
    <path d="m6 6 12 12M18 6 6 18" />
  {:else if name === "compass"}
    <circle cx="12" cy="12" r="9" /><path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" />
  {:else if name === "lens"}
    <circle cx="10.5" cy="10.5" r="6.5" /><path
      d="m15.5 15.5 4 4M8 11h5M10.5 8.5v5"
    />
  {:else if name === "map"}
    <path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z" /><path d="M9 3v15M15 6v15" />
  {:else if name === "menu"}
    <path d="M4 7h16M4 12h16M4 17h16" />
  {:else if name === "route"}
    <circle cx="5" cy="18" r="2" /><circle cx="19" cy="6" r="2" /><path
      d="M7 18h4a3 3 0 0 0 3-3V9a3 3 0 0 1 3-3"
    />
  {:else if name === "settings"}
    <circle cx="12" cy="12" r="3" /><path
      d="M12 2v3M12 19v3M4.9 4.9 7 7m10 10 2.1 2.1M2 12h3m14 0h3M4.9 19.1 7 17M17 7l2.1-2.1"
    />
  {:else if name === "sources"}
    <path d="M6 3h9l3 3v15H6V3Z" /><path d="M14 3v4h4M9 11h6M9 15h6" />
  {:else if name === "users"}
    <circle cx="9" cy="8" r="3" /><path
      d="M3 19a6 6 0 0 1 12 0M16 5.5a3 3 0 0 1 0 5.5M17 14a5 5 0 0 1 4 5"
    />
  {:else if name === "origin"}
    <circle cx="12" cy="8" r="3" /><path
      d="M5 20c1-5 3-7 7-7s6 2 7 7M4 4h3M17 4h3"
    />
  {:else if name === "place"}
    <path d="M12 21s7-7 7-13a7 7 0 1 0-14 0c0 6 7 13 7 13Z" /><circle
      cx="12"
      cy="8"
      r="2"
    />
  {:else if name === "work"}
    <path d="M4 5h16v14H4V5Z" /><path d="m7 15 3-4 2 2 2-3 3 5M8 8h.01" />
  {:else if name === "part"}
    <path d="M4 4h7v7H4V4ZM13 13h7v7h-7v-7ZM14 4h6v6M4 14h6v6" />
  {:else if name === "nature"}
    <path d="M20 4C10 4 5 9 5 16c4 1 11 0 15-12Z" /><path
      d="M4 20c4-6 8-9 13-12"
    />
  {:else if name === "influence"}
    <path d="M12 3v18M3 12h18M5.5 5.5l13 13M18.5 5.5l-13 13" />
  {/if}
</svg>
