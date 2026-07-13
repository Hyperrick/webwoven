<script lang="ts">
  import { tick } from "svelte";
  import type { SessionSnapshot } from "../api/types";
  import {
    buildMapBoard,
    type MapBoardNode,
    type MapMoveChoice,
  } from "../domain/map-board";
  import AtlasIcon from "./AtlasIcon.svelte";
  import MapBoardCanvas from "./MapBoardCanvas.svelte";

  let {
    session,
    busy = false,
    compassSelecting = false,
    onFollow,
    onCompassSelect,
  }: {
    session: SessionSnapshot;
    busy?: boolean;
    compassSelecting?: boolean;
    onFollow: (edgeToken: string) => void;
    onCompassSelect: (propertyId: string) => void;
  } = $props();

  interface WideningMapLayout {
    height_units: number;
    width_units?: number;
  }

  let viewport: HTMLDivElement;
  let activeColumnAnchor: HTMLSpanElement;
  let scrollRequest = 0;
  let hasCenteredOnce = false;

  let board = $derived(buildMapBoard(session));
  let nodesById = $derived(new Map(board.nodes.map((node) => [node.id, node])));
  let currentNode = $derived(nodesById.get(board.current_node_id));
  let goalNode = $derived(nodesById.get(board.goal_node_id));
  let choices = $derived(
    board.choices.filter((choice) => {
      const target = nodesById.get(choice.target_node_id);
      return (
        choice.source_node_id === board.current_node_id &&
        Boolean(choice.edge_token) &&
        !hasRole(target, "discarded")
      );
    }),
  );
  let goalChoice = $derived(
    choices.find((choice) => choice.target_node_id === board.goal_node_id),
  );
  let onwardChoices = $derived(
    choices.filter((choice) => choice.target_node_id !== board.goal_node_id),
  );
  let activeChoiceNodeIds = $derived(
    new Set(choices.map((choice) => choice.target_node_id)),
  );
  let historicalNodes = $derived(
    board.nodes.filter(
      (node) =>
        node.id !== board.current_node_id &&
        node.id !== board.goal_node_id &&
        !activeChoiceNodeIds.has(node.id) &&
        (hasRole(node, "trail") || hasRole(node, "discarded")),
    ),
  );
  let visitsByNodeId = $derived(
    new Map(board.trail.map((visit) => [visit.node_id, visit])),
  );
  let activeColumnX = $derived.by(() => {
    const activeNodes = choices
      .map((choice) => nodesById.get(choice.target_node_id))
      .filter((node): node is MapBoardNode => node !== undefined);
    if (activeNodes.length === 0) return currentNode?.position.x ?? 0.5;
    return (
      activeNodes.reduce((total, node) => total + node.position.x, 0) /
      activeNodes.length
    );
  });
  let boardStyle = $derived(
    `--map-min-height: ${board.layout.height_units}rem; --map-world-width: ${mapWidth(board.layout)}`,
  );

  $effect(() => {
    const stateVersion = session.state_version;
    const columnX = activeColumnX;
    const worldWidth = mapWidth(board.layout);
    const request = ++scrollRequest;
    void stateVersion;
    void worldWidth;

    void tick().then(() => {
      if (request !== scrollRequest || !viewport || !activeColumnAnchor) return;
      const centeredLeft =
        activeColumnAnchor.offsetLeft - viewport.clientWidth / 2;
      const maximumLeft = Math.max(
        0,
        viewport.scrollWidth - viewport.clientWidth,
      );
      const reducedMotion =
        document.documentElement.dataset.motion === "reduced" ||
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      viewport.scrollTo({
        left: Math.min(maximumLeft, Math.max(0, centeredLeft)),
        behavior: hasCenteredOnce && !reducedMotion ? "smooth" : "auto",
      });
      hasCenteredOnce = true;
    });
    void columnX;
  });

  function mapWidth(layout: WideningMapLayout): string {
    return layout.width_units && layout.width_units > 0
      ? `${layout.width_units}rem`
      : "100%";
  }

  function hasRole(node: MapBoardNode | undefined, role: string): boolean {
    return Boolean(node && (node.roles as readonly string[]).includes(role));
  }

  function positionStyle(node: MapBoardNode | undefined): string {
    if (!node) return "--node-x: 50%; --node-y: 50%";
    return `--node-x: ${node.position.x * 100}%; --node-y: ${node.position.y * 100}%`;
  }

  function choicePositionStyle(choice: MapMoveChoice): string {
    return positionStyle(nodesById.get(choice.target_node_id));
  }

  function activeColumnStyle(): string {
    return `--node-x: ${activeColumnX * 100}%`;
  }

  function choose(choice: MapMoveChoice): void {
    if (compassSelecting) onCompassSelect(choice.relation.property_id);
    else if (choice.edge_token) onFollow(choice.edge_token);
  }

  function statementParts(
    statement: string,
    targetLabel: string,
  ): { before: string; match: string; after: string } | null {
    const index = statement
      .toLocaleLowerCase("en")
      .indexOf(targetLabel.toLocaleLowerCase("en"));
    if (index < 0) return null;
    return {
      before: statement.slice(0, index),
      match: statement.slice(index, index + targetLabel.length),
      after: statement.slice(index + targetLabel.length),
    };
  }

  function connectionSummary(choice: MapMoveChoice): string {
    return [
      ...new Set(choice.connections.map(({ statement }) => statement)),
    ].join(" ");
  }
</script>

<section
  class="game-map"
  class:game-map--compass={compassSelecting}
  aria-labelledby="map-title"
  aria-describedby="map-instruction"
>
  <header class="game-map__header">
    <div class="game-map__prompt">
      <p class="eyebrow">
        {compassSelecting ? "Compass ready" : "Your move"}
      </p>
      <h2 id="map-title">
        {compassSelecting
          ? "Which route should the Compass check?"
          : "Where do you go next?"}
      </h2>
      <p id="map-instruction">
        {compassSelecting
          ? "Select a connected entity to evaluate that relationship. This uses the Compass but does not move you."
          : "Pick one connected entity. Each route shows the fact that joins it to your current position."}
      </p>
    </div>

    <p class="game-map__choice-count" aria-live="polite">
      <strong>{choices.length}</strong>
      {choices.length === 1 ? "route" : "routes"} in reach
    </p>
  </header>

  <!-- svelte-ignore a11y_no_noninteractive_tabindex (keyboard-scrollable map viewport) -->
  <div
    class="game-map__viewport"
    role="region"
    aria-label="Expanding route map"
    tabindex="0"
    bind:this={viewport}
  >
    <div class="game-map__surface" style={boardStyle}>
      <MapBoardCanvas {board} />
      <span
        class="game-map__active-column"
        style={activeColumnStyle()}
        aria-hidden="true"
        bind:this={activeColumnAnchor}
      ></span>

      <div class="game-map__history" aria-hidden="true">
        {#each historicalNodes as node (node.id)}
          {@const visit = visitsByNodeId.get(node.id)}
          <div
            class="map-history-node"
            class:map-history-node--breadcrumb={hasRole(node, "trail")}
            class:map-history-node--discarded={hasRole(node, "discarded") &&
              !hasRole(node, "trail")}
            style={positionStyle(node)}
          >
            <span class="map-history-node__kicker">
              {#if visit}
                {visit.index === 0 ? "Start" : `Move ${visit.index}`}
              {:else}
                Not taken
              {/if}
            </span>
            <strong>{node.label}</strong>
          </div>
        {/each}
      </div>

      {#if currentNode}
        <div
          class="map-position map-position--current"
          style={positionStyle(currentNode)}
          role="status"
          aria-live="polite"
        >
          <span class="map-position__kicker">You are here</span>
          <h3>{currentNode.label}</h3>
        </div>
      {/if}

      {#if goalNode}
        {#if goalChoice}
          {@const goalParts = statementParts(
            goalChoice.statement,
            goalChoice.target.label,
          )}
          <button
            type="button"
            class="map-position map-position--goal map-position--reachable"
            style={positionStyle(goalNode)}
            disabled={busy}
            aria-label={`${compassSelecting ? "Check" : "Finish"}: ${connectionSummary(goalChoice)}`}
            onclick={() => choose(goalChoice)}
          >
            <span class="map-position__kicker">Goal · in reach</span>
            {#if goalParts}
              <span class="map-position__fact">
                {goalParts.before}<strong>{goalParts.match}</strong
                >{goalParts.after}
              </span>
            {:else}
              <strong>{goalChoice.target.label}</strong>
              <span class="map-position__fact">{goalChoice.statement}</span>
            {/if}
            {#if goalChoice.connections.length > 1}
              <small class="map-position__connection-count">
                {goalChoice.connections.length} documented links
              </small>
            {/if}
            <span class="map-position__go">
              {compassSelecting ? "Check route" : "Finish here"}
              <AtlasIcon
                name={compassSelecting ? "compass" : "arrow"}
                size={18}
              />
            </span>
          </button>
        {:else}
          <div
            class="map-position map-position--goal"
            style={positionStyle(goalNode)}
          >
            <span class="map-position__kicker">Your goal</span>
            <h3>{goalNode.label}</h3>
            <span class="map-position__distance"
              >Find a route to this marker</span
            >
          </div>
        {/if}
      {/if}

      <div class="game-map__choices" aria-label="Connected entities">
        {#each onwardChoices as choice, index (choice.id)}
          {@const parts = statementParts(choice.statement, choice.target.label)}
          <button
            type="button"
            class:map-choice--promising={choice.relation.hint === "promising"}
            class="map-choice"
            style={choicePositionStyle(choice)}
            disabled={busy}
            aria-label={`${compassSelecting ? "Check" : "Go"}: ${connectionSummary(choice)}`}
            onclick={() => choose(choice)}
          >
            <span class="map-choice__number" aria-hidden="true">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span class="map-choice__icon" aria-hidden="true">
              <AtlasIcon name={choice.relation.glyph} size={20} />
            </span>
            <span class="map-choice__copy">
              {#if parts}
                <span class="map-choice__statement">
                  {parts.before}<strong>{parts.match}</strong>{parts.after}
                </span>
              {:else}
                <strong>{choice.target.label}</strong>
                <span>{choice.statement}</span>
              {/if}
              {#if choice.connections.length > 1}
                <small class="map-choice__connection-count">
                  {choice.connections.length} documented links
                </small>
              {/if}
            </span>
            <span class="map-choice__go">
              {compassSelecting ? "Check" : "Go"}
              <AtlasIcon
                name={compassSelecting ? "compass" : "arrow"}
                size={18}
              />
            </span>
          </button>
        {/each}
      </div>

      {#if choices.length === 0}
        <div
          class="game-map__dead-end"
          style={positionStyle(currentNode)}
          role="status"
        >
          <strong>No onward route from here.</strong>
          <span>Use Back to return to the previous marker.</span>
        </div>
      {/if}
    </div>
  </div>

  {#if session.last_connection}
    <p class="game-map__last-move" role="status">
      <strong>Last move</strong>
      <span>{session.last_connection}</span>
    </p>
  {/if}

  <ol class="game-map__trail">
    {#each board.trail as visit (visit.index)}
      <li
        aria-current={visit.index === board.trail.length - 1
          ? "step"
          : undefined}
      >
        {visit.index === 0 ? "Start" : `Move ${visit.index}`}: {visit.label}
        {#if visit.statement}
          — {visit.statement}{/if}
      </li>
    {/each}
  </ol>
</section>
