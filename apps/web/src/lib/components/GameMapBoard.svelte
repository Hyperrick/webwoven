<script lang="ts">
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

  let board = $derived(buildMapBoard(session));
  let nodesById = $derived(new Map(board.nodes.map((node) => [node.id, node])));
  let currentNode = $derived(nodesById.get(board.current_node_id));
  let goalNode = $derived(nodesById.get(board.goal_node_id));
  let choices = $derived(board.choices);
  let goalChoice = $derived(
    choices.find((choice) => choice.target_node_id === board.goal_node_id),
  );
  let onwardChoices = $derived(
    choices.filter((choice) => choice.target_node_id !== board.goal_node_id),
  );
  let boardStyle = $derived(
    `--map-min-height: ${board.layout.height_units}rem`,
  );

  function positionStyle(node: MapBoardNode | undefined): string {
    if (!node) return "--node-x: 50%; --node-y: 50%";
    return `--node-x: ${node.position.x * 100}%; --node-y: ${node.position.y * 100}%`;
  }

  function choicePositionStyle(choice: MapMoveChoice): string {
    return positionStyle(nodesById.get(choice.target_node_id));
  }

  function choose(choice: MapMoveChoice): void {
    if (compassSelecting) onCompassSelect(choice.relation.property_id);
    else onFollow(choice.edge_token);
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
  style={boardStyle}
  aria-labelledby="map-title"
  aria-describedby="map-instruction"
>
  <MapBoardCanvas {board} />

  <header class="game-map__prompt">
    <p class="eyebrow">{compassSelecting ? "Compass ready" : "Your move"}</p>
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
  </header>

  <p class="game-map__choice-count" aria-live="polite">
    <strong>{choices.length}</strong>
    {choices.length === 1 ? "route" : "routes"} in reach
  </p>

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
          <AtlasIcon name={compassSelecting ? "compass" : "arrow"} size={18} />
        </span>
      </button>
    {:else}
      <div
        class="map-position map-position--goal"
        style={positionStyle(goalNode)}
      >
        <span class="map-position__kicker">Your goal</span>
        <h3>{goalNode.label}</h3>
        <span class="map-position__distance">Find a route to this marker</span>
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
          <AtlasIcon name={compassSelecting ? "compass" : "arrow"} size={18} />
        </span>
      </button>
    {/each}
  </div>

  {#if choices.length === 0}
    <div class="game-map__dead-end" role="status">
      <strong>No onward route from here.</strong>
      <span>Use Back to return to the previous marker.</span>
    </div>
  {/if}

  {#if session.last_connection}
    <p class="game-map__last-move" role="status">
      <strong>Last move</strong>
      <span>{session.last_connection}</span>
    </p>
  {/if}

  <ol class="game-map__trail">
    {#each board.trail as visit (visit.index)}
      <li
        aria-current={visit.node_id === board.current_node_id
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
