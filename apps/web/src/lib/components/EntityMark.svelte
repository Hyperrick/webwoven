<script lang="ts">
  import type { Category } from "../api/types";

  let { category, label }: { category: Category; label: string } = $props();
</script>

<div
  class="entity-mark entity-mark--{category}"
  role="img"
  aria-label={`Atlas illustration for ${label}`}
>
  <svg viewBox="0 0 520 360" aria-hidden="true">
    <path
      class="entity-mark__contour entity-mark__contour--one"
      d="M-20 86c88-48 129 35 215-3 84-38 129-11 180 17 57 31 113-4 169-43"
    />
    <path
      class="entity-mark__contour entity-mark__contour--two"
      d="M-11 279c71-77 154-37 211-84 55-45 90-32 135 5 59 50 125 8 201-28"
    />
    <path
      class="entity-mark__contour entity-mark__contour--three"
      d="M39 355c52-79 141-72 190-112 45-36 85-19 119 18 48 52 92 46 178-8"
    />
    {#if category === "nature_science"}
      <path
        class="entity-mark__subject"
        d="M104 182c69-51 137-52 210-7 32 20 69 20 112-6-19 35-54 55-100 58-69 5-132-10-188-44-12 17-29 29-52 36 12-13 18-26 18-37Z"
      />
      <path
        class="entity-mark__detail"
        d="M167 181c5-29 26-48 61-57-8 28-3 46 15 58M371 188c25 4 43 18 53 42"
      />
    {:else if category === "places"}
      <path
        class="entity-mark__subject"
        d="m110 232 82-100 49 48 49-92 118 144H110Z"
      />
      <path
        class="entity-mark__detail"
        d="m153 180 39-48 16 16m42 16 40-76 37 45"
      />
    {:else if category === "arts_culture"}
      <path
        class="entity-mark__subject"
        d="M116 225c47-105 105-104 173 3 26-68 70-88 132-61-41-3-68 21-83 72H117Z"
      />
      <path
        class="entity-mark__detail"
        d="M146 213c39-70 79-66 120 12M319 205c25-36 52-46 83-29"
      />
    {:else}
      <path
        class="entity-mark__subject"
        d="M150 244v-93h45v-37h47v57h39V89h53v155H150Z"
      />
      <path class="entity-mark__detail" d="M177 151v93m42-130v130m89-155v155" />
    {/if}
    <circle class="entity-mark__pin" cx="405" cy="76" r="7" />
    <path class="entity-mark__pin-line" d="M405 83v38" />
  </svg>
  <span class="entity-mark__index">{label.slice(0, 2).toUpperCase()}</span>
</div>
