<script lang="ts">
  import { tick } from "svelte";
  import type { Difficulty, RoomSnapshot, RoundFilters } from "../api/types";
  import AtlasIcon from "../components/AtlasIcon.svelte";
  import CategoryPicker from "../components/CategoryPicker.svelte";
  import DifficultyPicker from "../components/DifficultyPicker.svelte";
  import LobbyCodeShare from "../components/LobbyCodeShare.svelte";
  import {
    loadCategoryFilter,
    persistCategoryFilter,
    roundFilters,
  } from "../round-setup/category-filter";
  import { loadDifficulty, persistDifficulty } from "../round-setup/difficulty";

  let {
    room,
    busy = false,
    onCreate,
    onJoin,
    onReady,
    onStart,
  }: {
    room?: RoomSnapshot;
    busy?: boolean;
    onCreate: (filters: RoundFilters) => void;
    onJoin: (code: string) => void;
    onReady: () => void;
    onStart: () => void;
  } = $props();

  let code = $state("");
  let relayDifficulty = $state<Difficulty>(loadDifficulty("relay"));
  let relayCategory = $state(loadCategoryFilter("relay"));
  let lobbyHeader = $state<HTMLElement>();
  let revealedLobbyCode = $state("");
  let allReady = $derived(
    room?.players.every((player) => player.ready) ?? false,
  );
  let currentPlayer = $derived(
    room?.players.find((player) => player.is_current_guest),
  );

  $effect(() => {
    const nextCode = room?.code;
    const header = lobbyHeader;
    if (!nextCode || !header || nextCode === revealedLobbyCode) return;
    revealedLobbyCode = nextCode;
    if (!window.matchMedia("(width <= 50rem)").matches) return;
    void tick().then(() =>
      window.requestAnimationFrame(() =>
        header.scrollIntoView({ block: "start", behavior: "auto" }),
      ),
    );
  });

  function createRoom(): void {
    persistDifficulty("relay", relayDifficulty);
    persistCategoryFilter("relay", relayCategory);
    onCreate(roundFilters(relayDifficulty, relayCategory));
  }

  function titleCase(value: string): string {
    return value
      .split("_")
      .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
      .join(" & ");
  }
</script>

<main class="lobby-page">
  {#if !room}
    <section class="lobby-intro">
      <div>
        <p class="eyebrow">Multiplayer lobby</p>
        <h1>One atlas.<br /><em>Several instincts.</em></h1>
        <p>
          Two to four players receive the same route. You’ll see how close the
          others are—never where they are.
        </p>
      </div>

      <div class="lobby-entry">
        <section>
          <span class="lobby-entry__number">01</span>
          <h2>Open a lobby</h2>
          <p>
            Receive a short field code and invite up to three other explorers.
          </p>
          <CategoryPicker
            id="relay-category"
            bind:value={relayCategory}
            disabled={busy}
          />
          <DifficultyPicker
            bind:value={relayDifficulty}
            legend="Game difficulty"
            disabled={busy}
          />
          <button
            class="primary-action"
            type="button"
            disabled={busy}
            onclick={createRoom}
          >
            Create lobby <AtlasIcon name="arrow" size={20} />
          </button>
        </section>
        <section>
          <span class="lobby-entry__number">02</span>
          <h2>Join a lobby</h2>
          <p>Enter the code from your expedition host.</p>
          <form
            onsubmit={(event) => {
              event.preventDefault();
              if (code.trim()) onJoin(code);
            }}
          >
            <label for="room-code">Lobby code</label>
            <div class="code-entry">
              <input
                id="room-code"
                bind:value={code}
                maxlength="6"
                autocomplete="off"
                placeholder="MAPS27"
              />
              <button
                type="submit"
                disabled={busy || !code.trim()}
                aria-label="Join lobby"
                ><AtlasIcon name="arrow" size={21} /></button
              >
            </div>
          </form>
        </section>
      </div>
    </section>
  {:else}
    <section class="room-sheet" aria-labelledby="room-title">
      <header bind:this={lobbyHeader} class="room-sheet__header">
        <div>
          <p class="eyebrow">Lobby</p>
          <h1 id="room-title">Ready the map.</h1>
        </div>
        <LobbyCodeShare
          code={room.code}
          hostDisplayName={currentPlayer?.display_name ?? "Your host"}
          shareable={currentPlayer?.is_host ?? false}
        />
      </header>

      <div class="room-route-stamp" aria-label="Locked lobby route settings">
        <span>Locked route</span>
        <strong
          >{titleCase(room.category)} · {titleCase(room.difficulty)}</strong
        >
        <small>{room.start.label} → {room.target.label}</small>
      </div>

      <div class="room-sheet__body">
        <section class="roster" aria-labelledby="roster-title">
          <div class="roster__heading">
            <h2 id="roster-title">Field team</h2>
            <span>{room.players.length} / {room.max_players}</span>
          </div>
          <ol>
            {#each room.players as player, index (player.id)}
              <li>
                <span class="roster__index"
                  >{String(index + 1).padStart(2, "0")}</span
                >
                <span class="roster__person"
                  ><strong>{player.display_name}</strong><small
                    >{player.is_host
                      ? "Host"
                      : "Explorer"}{player.is_current_guest
                      ? " · You"
                      : ""}</small
                  ></span
                >
                <span
                  class:roster__state--ready={player.ready}
                  class="roster__state"
                >
                  {player.ready ? "Ready" : "Checking map"}
                </span>
              </li>
            {/each}
          </ol>
        </section>

        <aside class="room-rules">
          <p class="eyebrow">How it works</p>
          <ol>
            <li>
              <span>01</span>Everyone receives the same start and destination.
            </li>
            <li><span>02</span>Only moves and broad progress are shared.</li>
            <li>
              <span>03</span>The first valid arrival starts a 30-second grace
              period.
            </li>
          </ol>
          <button
            class="secondary-action"
            type="button"
            disabled={busy}
            onclick={onReady}
          >
            {currentPlayer?.ready ? "Mark as not ready" : "I’m ready"}
          </button>
          {#if currentPlayer?.is_host}
            <button
              class="primary-action"
              type="button"
              disabled={busy || !allReady}
              onclick={onStart}
            >
              Start game <AtlasIcon name="arrow" size={20} />
            </button>
          {/if}
          {#if !allReady}<p class="room-rules__waiting" role="status">
              Waiting for every explorer to ready up.
            </p>{/if}
        </aside>
      </div>
    </section>
  {/if}
</main>
