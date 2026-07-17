<script lang="ts">
  import type { LandingRoutePreview } from "../domain/landing-route-preview";
  import {
    createLandingRouteMapLayout,
    type LandingRouteMapPoint,
  } from "../domain/landing-route-map";

  let { route }: { route: LandingRoutePreview } = $props();

  const gridColumns = [20, 40, 60, 80] as const;
  const gridRows = [20, 40, 60, 80] as const;
  const contourRings = [0, 1, 2] as const;
  let layout = $derived(
    createLandingRouteMapLayout(route.number, route.steps.length),
  );
  let routePath = $derived(
    layout.points
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
      .join(" "),
  );

  function pointStyle(point: LandingRouteMapPoint): string {
    return `--map-x: ${point.x}%; --map-y: ${point.y}%;`;
  }
</script>

<div class="landing-route-map" data-route-number={route.number}>
  <svg
    class="landing-route-map__drawing"
    viewBox="0 0 100 100"
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <g class="landing-route-map__grid">
      {#each gridColumns as column}
        <line x1={column} y1="0" x2={column} y2="100" />
      {/each}
      {#each gridRows as row}
        <line x1="0" y1={row} x2="100" y2={row} />
      {/each}
    </g>

    <g class="landing-route-map__folds">
      {#each layout.verticalFolds as fold}
        <line x1={fold} y1="0" x2={fold} y2="100" />
      {/each}
      {#each layout.horizontalFolds as fold}
        <line x1="0" y1={fold} x2="100" y2={fold} />
      {/each}
    </g>

    <g class="landing-route-map__contours">
      {#each layout.contours as contour}
        {#each contourRings as ring}
          <ellipse
            cx={contour.x}
            cy={contour.y}
            rx={contour.radiusX + ring * 2.4}
            ry={contour.radiusY + ring * 1.7}
          />
        {/each}
      {/each}
    </g>

    <path class="landing-route-map__route" d={routePath} />
    <line
      class="landing-route-map__known-segment"
      x1={layout.points[0].x}
      y1={layout.points[0].y}
      x2={layout.points[1].x}
      y2={layout.points[1].y}
    />
    <line
      class="landing-route-map__known-segment"
      x1={layout.points.at(-2)?.x}
      y1={layout.points.at(-2)?.y}
      x2={layout.points.at(-1)?.x}
      y2={layout.points.at(-1)?.y}
    />

    <g class="landing-route-map__registration">
      <path d="M 4 8 H 10 M 7 5 V 11" />
      <path d="M 90 92 H 96 M 93 89 V 95" />
    </g>
  </svg>

  <div class="landing-route-map__column-labels" aria-hidden="true">
    <span>A1</span><span>B2</span><span>C3</span><span>D4</span>
  </div>
  <div class="landing-route-map__row-labels" aria-hidden="true">
    <span>10</span><span>20</span><span>30</span><span>40</span>
  </div>

  <ol aria-label="Route waypoints">
    {#each route.steps as step, index}
      <li
        class="landing-route-map__waypoint"
        class:landing-route-map__waypoint--start={index === 0}
        class:landing-route-map__waypoint--goal={index ===
          route.steps.length - 1}
        class:hero-route__step--hidden={step.hidden}
        style={pointStyle(layout.points[index])}
      >
        {#if step.hidden}
          <span class="landing-route-map__sealed-node" aria-hidden="true">
            {step.number}
          </span>
          <strong aria-label="Connection hidden">{step.label}</strong>
        {:else}
          <span class="landing-route-map__endpoint-node" aria-hidden="true"
          ></span>
          <span class="landing-route-map__endpoint-copy">
            <small>{index === 0 ? "Start" : "Goal"} · {step.number}</small>
            <strong>{step.label}</strong>
          </span>
        {/if}
      </li>
    {/each}
  </ol>
</div>
