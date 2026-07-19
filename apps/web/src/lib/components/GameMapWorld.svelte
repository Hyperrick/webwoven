<script lang="ts">
  import { fade, slide } from "svelte/transition";
  import {
    type MapBoard,
    type MapBoardNode,
    type MapBoardNodeRole,
    type MapMoveChoice,
  } from "../domain/map-board";
  import type { MapTransition } from "../domain/map-transition";
  import AtlasIcon from "./AtlasIcon.svelte";
  import EndpointArtwork from "./EndpointArtwork.svelte";
  import MobileMapChoiceNode from "./MobileMapChoiceNode.svelte";
  import { observeMobileNodeLabel } from "./map-viewport/mobile-node-label-measure";

  let {
    board,
    transition,
    busy = false,
    canGoBack = false,
    compassSelecting = false,
    compactChoices = false,
    selectedChoiceId = null,
    backTargetNodeId = null,
    selectedBackNodeId = null,
    mobileNodeLabelLines = new Map(),
    mobileNodeRowLabelLines = new Map(),
    onChoose,
    onSelectChoice,
    onMobileNodeLabelMeasure,
    onBackNodeActivate,
    onBack,
    backDestinationLabel,
    onInspect,
  }: {
    board: MapBoard;
    transition: MapTransition;
    busy?: boolean;
    canGoBack?: boolean;
    compassSelecting?: boolean;
    compactChoices?: boolean;
    selectedChoiceId?: string | null;
    backTargetNodeId?: string | null;
    selectedBackNodeId?: string | null;
    mobileNodeLabelLines?: ReadonlyMap<string, number>;
    mobileNodeRowLabelLines?: ReadonlyMap<string, number>;
    onChoose: (choice: MapMoveChoice) => void;
    onSelectChoice: (choice: MapMoveChoice) => void;
    onMobileNodeLabelMeasure: (nodeId: string, lineCount: number) => void;
    onBackNodeActivate: (nodeId: string) => void;
    onBack: () => void;
    backDestinationLabel?: string;
    onInspect: (nodeId: string, anchor: HTMLElement) => void;
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

  function mobileLabelLines(nodeId: string): number {
    return (
      mobileNodeRowLabelLines.get(nodeId) ??
      mobileNodeLabelLines.get(nodeId) ??
      2
    );
  }

  function historyPositionStyle(node: MapBoardNode): string {
    return `${positionStyle(node)}; --mobile-history-label-lines: ${mobileLabelLines(node.id)}`;
  }

  function measureMobileNodeLabel(
    node: HTMLElement,
    nodeId: string,
  ): { destroy: () => void } {
    return observeMobileNodeLabel(node, (lineCount) =>
      onMobileNodeLabelMeasure(nodeId, lineCount),
    );
  }

  function hintLabel(hint: MapMoveChoice["relation"]["hint"]): string {
    if (hint === "dead_end") return "DEAD END";
    if (hint === "longer" || hint === "unlikely") return "LONGER ROUTE";
    return "PROMISING ROUTE";
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

  function activateCompactChoice(choice: MapMoveChoice): void {
    if (choice.id === selectedChoiceId) onChoose(choice);
    else onSelectChoice(choice);
  }

  function compactChoiceLabel(choice: MapMoveChoice): string {
    const summary = connectionSummary(choice);
    if (choice.id !== selectedChoiceId)
      return `Preview route to ${choice.target.label}: ${summary}`;
    if (compassSelecting)
      return `Check route to ${choice.target.label}: ${summary}`;
    if (choice.target_node_id === board.goal_node_id)
      return `Finish route to ${choice.target.label}: ${summary}`;
    return `Move to ${choice.target.label}: ${summary}`;
  }

  function inspectFrom(event: MouseEvent, nodeId: string): void {
    const target = event.currentTarget;
    if (target instanceof HTMLElement) onInspect(nodeId, target);
  }
</script>

<div class="game-map__history">
  {#each historicalNodes as node (node.id)}
    {@const visit = visitsByNodeId.get(node.id)}
    {@const taken = hasRole(node, "trail")}
    {@const nodeArtwork = node.summary}
    {@const backTarget = node.id === backTargetNodeId}
    {@const backReady = backTarget && node.id === selectedBackNodeId}
    <button
      type="button"
      class="map-history-node"
      class:map-history-node--with-artwork={Boolean(nodeArtwork) &&
        !compactChoices}
      class:map-history-node--breadcrumb={taken}
      class:map-history-node--discarded={hasRole(node, "discarded") && !taken}
      class:map-history-node--backtracked={transition.kind === "back" &&
        transition.from_node_id === node.id}
      class:map-history-node--back-target={backTarget}
      class:map-history-node--back-ready={backReady}
      style={historyPositionStyle(node)}
      disabled={busy && backTarget}
      data-map-node
      data-map-node-id={node.id}
      data-map-route={taken ? "true" : undefined}
      data-map-back-target={backTarget ? "true" : undefined}
      data-map-interactive={backTarget ? "back" : "inspect"}
      data-mobile-label-lines={mobileLabelLines(node.id)}
      aria-pressed={backTarget ? backReady : undefined}
      aria-label={backTarget
        ? `${backReady ? "Back" : "Preview Back"} to ${node.label}`
        : `Inspect ${node.label}, ${taken ? "route taken" : "route not taken"}`}
      onclick={(event) =>
        backTarget ? onBackNodeActivate(node.id) : inspectFrom(event, node.id)}
    >
      {#if nodeArtwork && !compactChoices}
        <EndpointArtwork
          entity={nodeArtwork}
          endpoint={hasRole(node, "start") ? "start" : "node"}
          className="map-history-node__artwork"
          loading="eager"
        />
      {/if}
      <span class="map-history-node__copy">
        <span class="map-history-node__kicker">
          {#if backReady}
            Back
          {:else if visit}
            {visit.index === 0 ? "Start" : `Move ${visit.index}`}
          {:else}
            Not taken
          {/if}
        </span>
        <strong use:measureMobileNodeLabel={node.id}>{node.label}</strong>
      </span>
      {#if backReady}
        <span class="map-history-node__back-confirm" aria-hidden="true">
          <AtlasIcon name="back" size={14} />
        </span>
      {/if}
    </button>
  {/each}
</div>

{#if currentNode}
  {#key currentNode.id}
    {@const currentArtwork = currentNode.summary}
    <div
      class="map-position map-position--current map-position--inspectable"
      class:map-position--with-artwork={Boolean(currentArtwork)}
      style={positionStyle(currentNode)}
      data-map-node
      data-map-node-id={currentNode.id}
      data-map-current="true"
      data-map-focus="current"
      data-mobile-label-lines={mobileLabelLines(currentNode.id)}
      role="status"
      aria-live="polite"
      in:fade={{
        duration:
          transition.kind === "back" || transition.kind === "dead_end_back"
            ? 260
            : 160,
      }}
      out:fade={{ duration: 180 }}
    >
      <button
        type="button"
        class="map-position__inspect-hit-area"
        data-map-interactive="inspect"
        aria-label={`Inspect current entity: ${currentNode.label}`}
        onclick={(event) => inspectFrom(event, currentNode.id)}
      ></button>
      {#if currentArtwork}
        <EndpointArtwork
          entity={currentArtwork}
          endpoint={hasRole(currentNode, "start") ? "start" : "node"}
          className="map-position__artwork"
          loading="eager"
        />
      {/if}
      <span class="map-position__kicker">You are here</span>
      <h3 use:measureMobileNodeLabel={currentNode.id}>{currentNode.label}</h3>
      <span class="map-position__inspect-button" aria-hidden="true">
        Inspect
      </span>
    </div>
  {/key}
{/if}

{#if goalNode && (!compactChoices || !goalChoice)}
  {#if goalChoice}
    {@const goalParts = statementParts(
      goalChoice.statement,
      goalChoice.target.label,
    )}
    <button
      type="button"
      class:map-position--hint-promising={goalChoice.relation.hint ===
        "promising"}
      class:map-position--hint-longer={goalChoice.relation.hint === "longer" ||
        goalChoice.relation.hint === "unlikely"}
      class:map-position--hint-dead-end={goalChoice.relation.hint ===
        "dead_end"}
      class="map-position map-position--goal map-position--reachable"
      style={positionStyle(goalNode)}
      disabled={busy}
      data-map-node
      data-map-node-id={goalNode.id}
      data-map-focus="goal"
      data-map-near-focus="goal"
      data-map-interactive="move"
      data-relation-kind={goalChoice.relation.glyph}
      aria-label={`${compassSelecting ? "Check" : "Finish"}: ${connectionSummary(goalChoice)}`}
      onclick={() => onChoose(goalChoice)}
    >
      <span
        class="map-position__goal-card map-position__goal-card--with-artwork"
      >
        <span class="map-choice__relation-mark" aria-hidden="true">
          <AtlasIcon name={goalChoice.relation.glyph} size={20} />
        </span>
        <span class="map-position__goal-copy">
          {#if goalChoice.relation.hint}
            <span class="map-choice__hint">
              {hintLabel(goalChoice.relation.hint)}
            </span>
          {/if}
          {#if goalParts}
            <span class="map-position__fact">
              {goalParts.before}<strong>{goalParts.match}</strong
              >{goalParts.after}
            </span>
          {:else}
            <strong>{goalChoice.target.label}</strong>
            <span class="map-position__fact">{goalChoice.statement}</span>
          {/if}
        </span>
        <EndpointArtwork
          entity={goalChoice.target}
          endpoint="goal"
          className="map-position__goal-artwork"
          loading="eager"
        />
        <span class="map-position__go">
          {compassSelecting ? "CHECK ROUTE" : "FINISH ROUTE"}
          <AtlasIcon name={compassSelecting ? "compass" : "arrow"} size={18} />
        </span>
      </span>
    </button>
  {:else}
    <div
      class="map-position map-position--goal"
      class:map-position--with-artwork={Boolean(goalNode.summary) &&
        !compactChoices}
      class:map-position--mobile-goal={compactChoices}
      style={positionStyle(goalNode)}
      data-map-node
      data-map-node-id={goalNode.id}
      data-map-goal="true"
      data-mobile-label-lines={mobileLabelLines(goalNode.id)}
    >
      {#if compactChoices}
        <span class="map-position__kicker">Goal</span>
        <h3 use:measureMobileNodeLabel={goalNode.id}>{goalNode.label}</h3>
      {:else}
        {#if goalNode.summary}
          <EndpointArtwork
            entity={goalNode.summary}
            endpoint="goal"
            className="map-position__artwork"
            loading="eager"
          />
        {/if}
        <span class="map-position__kicker">Your goal</span>
        <h3 use:measureMobileNodeLabel={goalNode.id}>{goalNode.label}</h3>
        <span class="map-position__distance">Find a route to this marker</span>
      {/if}
    </div>
  {/if}
{/if}

<div class="game-map__choices" aria-label="Connected entities">
  {#if compactChoices}
    {#each choices as choice, index (choice.id)}
      <MobileMapChoiceNode
        {choice}
        positionStyle={choicePositionStyle(choice)}
        selected={choice.id === selectedChoiceId}
        {busy}
        goal={choice.target_node_id === board.goal_node_id}
        nearFocus={index < 2}
        hintLabel={choice.relation.hint
          ? hintLabel(choice.relation.hint)
          : undefined}
        ariaLabel={compactChoiceLabel(choice)}
        confirmIcon={compassSelecting ? "compass" : "arrow"}
        rowLabelLines={mobileNodeRowLabelLines.get(choice.target_node_id) ?? 2}
        onActivate={activateCompactChoice}
        onLabelMeasure={onMobileNodeLabelMeasure}
      />
    {/each}
  {:else}
    {#each onwardChoices as choice, index (choice.id)}
      {@const parts = statementParts(choice.statement, choice.target.label)}
      <button
        type="button"
        class:map-choice--promising={choice.relation.hint === "promising"}
        class:map-choice--longer={choice.relation.hint === "longer" ||
          choice.relation.hint === "unlikely"}
        class:map-choice--dead-end={choice.relation.hint === "dead_end"}
        class="map-choice"
        style={choicePositionStyle(choice)}
        disabled={busy}
        data-map-node
        data-map-node-id={choice.target_node_id}
        data-map-focus="choice"
        data-map-near-focus={index < 2 ? "choice" : undefined}
        data-map-interactive="move"
        data-relation-kind={choice.relation.glyph}
        aria-label={`${compassSelecting ? `Check route to ${choice.target.label}` : `Move to ${choice.target.label}`}: ${connectionSummary(choice)}`}
        onclick={() => onChoose(choice)}
      >
        <span class="map-choice__relation-mark" aria-hidden="true">
          <AtlasIcon name={choice.relation.glyph} size={20} />
        </span>
        <span class="map-choice__copy">
          {#if choice.relation.hint}
            <small class="map-choice__hint">
              {hintLabel(choice.relation.hint)}
            </small>
          {/if}
          {#if parts}
            <span class="map-choice__statement">
              {parts.before}<strong>{parts.match}</strong>{parts.after}
            </span>
          {:else}
            <strong>{choice.target.label}</strong>
            <span>{choice.statement}</span>
          {/if}
        </span>
        <span class="map-choice__visual" aria-hidden="true">
          <EndpointArtwork
            entity={choice.target}
            endpoint="node"
            className="map-choice__artwork"
            loading="eager"
          />
        </span>
      </button>
    {/each}
  {/if}
</div>

{#if choices.length === 0}
  <div
    class="game-map__dead-end"
    style={positionStyle(currentNode)}
    data-map-focus="dead-end"
    data-map-near-focus="dead-end"
    role="group"
    aria-labelledby="dead-end-title"
    out:slide={{ duration: 180, axis: "y" }}
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
