<script lang="ts">
  import type { Category } from "../api/types";

  const CATEGORY_ARTWORK = {
    history_people: {
      label: "History & People",
      src: "/illustrations/history-people.webp",
    },
    nature_science: {
      label: "Nature & Science",
      src: "/illustrations/nature-science.webp",
    },
    arts_culture: {
      label: "Arts & Culture",
      src: "/illustrations/arts-culture.webp",
    },
    places: {
      label: "Places",
      src: "/illustrations/places.webp",
    },
  } satisfies Record<Category, { label: string; src: string }>;

  let { category, label }: { category: Category; label: string } = $props();

  const artwork = $derived(CATEGORY_ARTWORK[category]);
  const accessibilityLabel = $derived(
    `No reviewed documentary image is available for ${label}, so a branded ${artwork.label} category illustration is shown.`,
  );
</script>

<div
  class="entity-mark entity-mark--{category}"
  role="img"
  aria-label={accessibilityLabel}
>
  <img
    class="entity-mark__plate"
    src={artwork.src}
    alt=""
    width="1448"
    height="1086"
    loading="eager"
    decoding="async"
    fetchpriority="high"
    aria-hidden="true"
  />
  <span class="entity-mark__index" aria-hidden="true"
    >{label.slice(0, 2).toUpperCase()}</span
  >
</div>
