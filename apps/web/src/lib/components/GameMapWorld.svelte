<script lang="ts">
  import {
    type MapBoard,
    type MapBoardNode,
    type MapBoardNodeRole,
    type MapMoveChoice,
  } from "../domain/map-board";
  import AtlasIcon from "./AtlasIcon.svelte";

  let {
    board,
    busy = false,
    canGoBack = false,
    compassSelecting = false,
    onChoose,
    onBack,
    backDestinationLabel,
    onInspect,
  }: {
    board: MapBoard;
    busy?: boolean;
    canGoBack?: boolean;
    compassSelecting?: boolean;
    onChoose: (choice: MapMoveChoice) => void;
    onBack: () => void;
    backDestinationLabel?: string;
    onInspect: (nodeId: string) => void;
  } = $props();

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
  let historicalNodes = $derived(
    board.nodes.filter(
      (node) =>
        node.id !== board.current_node_id &&
        node.id !== board.goal_node_id &&
        (hasRole(node, "trail") || hasRole(node, "discarded")),
    ),
  );
  let visitsByNodeId = $derived(
    new Map(board.trail.map((visit) => [visit.node_id, visit])),
  );
  function hasRole(
    node: MapBoardNode | undefined,
    role: MapBoardNodeRole,
  ): boolean {
    return Boolean(node?.roles.includes(role));
  }

  function positionStyle(node: MapBoardNode | undefined): string {
    if (!node) return "--node-x: 50%; --node-y: 50%";
    return `--node-x: ${node.position.x * 100}%; --node-y: ${node.position.y * 100}%`;
  }

  function choicePositionStyle(choice: MapMoveChoice): string {
    return positionStyle(nodesById.get(choice.target_node_id));
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

<div class="game-map__history">
  {#each historicalNodes as node (node.id)}
    {@const visit = visitsByNodeId.get(node.id)}
    {@const taken = hasRole(node, "trail")}
    <button
      type="button"
      class="map-history-node"
      class:map-history-node--breadcrumb={taken}
      class:map-history-node--discarded={hasRole(node, "discarded") && !taken}
      style={positionStyle(node)}
      data-map-node
      data-map-node-id={node.id}
      data-map-route={taken ? "true" : undefined}
      data-map-interactive="inspect"
      aria-label={`Inspect ${node.label}, ${taken ? "route taken" : "route not taken"}`}
      onclick={() => onInspect(node.id)}
    >
      <span class="map-history-node__kicker">
        {#if visit}
          {visit.index === 0 ? "Start" : `Move ${visit.index}`}
        {:else}
          Not taken
        {/if}
      </span>
      <strong>{node.label}</strong>
    </button>
  {/each}
</div>

{#if currentNode}
  <div
    class="map-position map-position--current map-position--inspectable"
    style={positionStyle(currentNode)}
    data-map-node
    data-map-node-id={currentNode.id}
    data-map-current="true"
    data-map-focus="current"
    role="status"
    aria-live="polite"
  >
    <span class="map-position__kicker">You are here</span>
    <h3>{currentNode.label}</h3>
    <button
      type="button"
      class="map-position__inspect-button"
      data-map-interactive="inspect"
      aria-label={`Inspect current entity: ${currentNode.label}`}
      onclick={() => onInspect(currentNode.id)}
    >
      Inspect
    </button>
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
      data-map-node
      data-map-node-id={goalNode.id}
      data-map-focus="goal"
      data-map-near-focus="goal"
      data-map-interactive="move"
      aria-label={`${compassSelecting ? "Check" : "Finish"}: ${connectionSummary(goalChoice)}`}
      onclick={() => onChoose(goalChoice)}
    >
      <span class="map-position__kicker">Goal · in reach</span>
      {#if goalParts}
        <span class="map-position__fact">
          {goalParts.before}<strong>{goalParts.match}</strong>{goalParts.after}
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
      data-map-node
      data-map-node-id={goalNode.id}
      data-map-goal="true"
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
      data-map-node
      data-map-node-id={choice.target_node_id}
      data-map-focus="choice"
      data-map-near-focus={index < 2 ? "choice" : undefined}
      data-map-interactive="move"
      aria-label={`${compassSelecting ? `Check route to ${choice.target.label}` : `Move to ${choice.target.label}`}: ${connectionSummary(choice)}`}
      onclick={() => onChoose(choice)}
    >
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
    </button>
  {/each}
</div>

{#if choices.length === 0}
  <div
    class="game-map__dead-end"
    style={positionStyle(currentNode)}
    data-map-focus="dead-end"
    data-map-near-focus="dead-end"
    role="group"
    aria-labelledby="dead-end-title"
  >
    <div
      class="game-map__dead-end-status"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <span class="game-map__dead-end-kicker">Dead end</span>
      <strong id="dead-end-title">
        No routes from {currentNode?.label ?? "this marker"}
      </strong>
      <span>
        {canGoBack
          ? "Retrace one move and try another branch."
          : "No playable route is available from this start."}
      </span>
    </div>
    {#if canGoBack && backDestinationLabel}
      <button
        type="button"
        class="game-map__dead-end-back"
        disabled={busy}
        aria-describedby="dead-end-cost"
        data-map-interactive="back"
        onclick={onBack}
      >
        <AtlasIcon name="back" size={18} />
        <span>Back to {backDestinationLabel}</span>
        <kbd aria-hidden="true">B</kbd>
      </button>
      <small id="dead-end-cost" class="game-map__dead-end-cost">
        Counts as 1 move
      </small>
    {/if}
  </div>
{/if}
