<script lang="ts">
  import { onMount } from "svelte";
  import {
    RoomEventStream,
    type RelayConnectionState,
  } from "./lib/api/room-event-stream";
  import { createRuntimeApi } from "./lib/api/runtime-api";
  import type {
    HintType,
    LeaderboardEntry,
    RoomSnapshot,
    SessionSnapshot,
  } from "./lib/api/types";
  import SettingsDrawer from "./lib/components/SettingsDrawer.svelte";
  import SiteHeader from "./lib/components/SiteHeader.svelte";
  import SourcesDrawer from "./lib/components/SourcesDrawer.svelte";
  import ExitDialog from "./lib/components/ExitDialog.svelte";
  import StatusToast from "./lib/components/StatusToast.svelte";
  import { GameController } from "./lib/controllers/game-controller";
  import { RoomController } from "./lib/controllers/room-controller";
  import {
    BrowserRouter,
    parseRoute,
    type AppRoute,
  } from "./lib/navigation/router";
  import {
    clearActiveSession,
    loadActiveSessionId,
    persistActiveSession,
  } from "./lib/navigation/active-session";
  import {
    DEFAULT_PREFERENCES,
    loadPreferences,
    persistPreferences,
    type Preferences,
  } from "./lib/preferences/preferences";
  import GamePage from "./lib/pages/GamePage.svelte";
  import LabPage from "./lib/pages/LabPage.svelte";
  import LandingPage from "./lib/pages/LandingPage.svelte";
  import LobbyPage from "./lib/pages/LobbyPage.svelte";
  import NotFoundPage from "./lib/pages/NotFoundPage.svelte";
  import ResultsPage from "./lib/pages/ResultsPage.svelte";

  const api = createRuntimeApi();
  const games = new GameController(api);
  const rooms = new RoomController(api);
  const roomEvents = new RoomEventStream();

  let route = $state<AppRoute>(parseRoute(window.location.pathname));
  let session = $state<SessionSnapshot>();
  let room = $state<RoomSnapshot>();
  let leaderboard = $state<LeaderboardEntry[]>([]);
  let preferences = $state<Preferences>(DEFAULT_PREFERENCES);
  let drawer = $state<"settings" | "sources" | null>(null);
  let busy = $state(false);
  let error = $state("");
  let toast = $state("");
  let exitOpen = $state(false);
  let graphBuild = $state("loading-atlas");
  let relayConnection = $state<RelayConnectionState>("connected");
  let router: BrowserRouter;

  const hasProtectedGame = () =>
    session?.status === "active" &&
    ["solo", "daily", "race"].includes(route.name);

  onMount(() => {
    preferences = loadPreferences();
    persistPreferences(preferences);
    router = new BrowserRouter({
      isProtected: hasProtectedGame,
      onRoute: (next) => {
        if (next.name !== "race") roomEvents.stop();
        route = next;
        void hydrateRoute(next);
      },
      onBlockedNavigation: () => (exitOpen = true),
    });
    const stop = router.start();
    void run(initialize);
    return () => {
      stop();
      roomEvents.stop();
    };
  });

  async function initialize(): Promise<void> {
    try {
      await api.getGuest();
    } catch {
      await api.createGuest();
    }
    const config = await api.getConfig();
    graphBuild = config.graph_build;
    await hydrateRoute(route);
  }

  async function hydrateRoute(next: AppRoute): Promise<void> {
    if ((next.name === "solo" || next.name === "daily") && !session) {
      await restoreOrStartSession(next.name);
    }
    if (next.name === "race" && (!room || room.code !== next.code)) {
      await run(async () => {
        room = await rooms.join(next.code);
        session = room.current_session_id
          ? await games.resume(room.current_session_id)
          : await games.start("solo");
        connectRoomEvents(room.code);
      });
    }
    if (
      next.name === "results" &&
      session?.mode === "daily" &&
      leaderboard.length === 0
    ) {
      leaderboard = await api.getDailyLeaderboard();
    }
  }

  function navigate(path: string, bypassGuard = false): void {
    router?.navigate(path, { bypassGuard });
  }

  function begin(mode: "solo" | "daily"): void {
    clearActiveSession(mode);
    session = undefined;
    navigate(`/play/${mode}`);
  }

  async function restoreOrStartSession(mode: "solo" | "daily"): Promise<void> {
    await run(async () => {
      const storedId = loadActiveSessionId(mode);
      if (storedId) {
        try {
          const restored = await games.resume(storedId);
          if (restored.mode === mode && restored.status === "active") {
            session = restored;
            persistActiveSession(restored);
            return;
          }
        } catch {
          // A removed or graph-incompatible session starts cleanly below.
        }
        clearActiveSession(mode);
      }
      session = await createNewSession(mode);
      persistActiveSession(session);
    });
  }

  async function createNewSession(
    mode: "solo" | "daily",
  ): Promise<SessionSnapshot> {
    const round = mode === "daily" ? await api.getDaily() : undefined;
    const created = await games.start(mode, round?.round_id);
    return round
      ? { ...created, shortest_distance: round.optimal_distance }
      : created;
  }

  async function follow(edgeToken: string): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await games.follow(session!, edgeToken);
      persistActiveSession(session);
      if (session.status === "completed") {
        if (session.mode === "daily")
          leaderboard = await api.getDailyLeaderboard();
        window.setTimeout(() => navigate("/results", true), 300);
      }
    });
  }

  async function back(): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await games.back(session!);
      persistActiveSession(session);
    });
  }

  async function useHint(type: HintType, propertyId?: string): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await games.hint(session!, type, propertyId);
      persistActiveSession(session);
    });
  }

  async function createRoom(): Promise<void> {
    await run(async () => {
      room = await rooms.create();
    });
  }

  async function joinRoom(code: string): Promise<void> {
    await run(async () => {
      room = await rooms.join(code);
    });
  }

  async function toggleReady(): Promise<void> {
    if (!room) return;
    await run(async () => {
      room = await rooms.toggleReady(room!);
    });
  }

  async function startRelay(): Promise<void> {
    if (!room) return;
    await run(async () => {
      room = await rooms.start(room!);
      navigate(`/relay/${room.code}`);
      session = room.current_session_id
        ? await games.resume(room.current_session_id)
        : await games.start("solo");
      connectRoomEvents(room.code);
    });
  }

  async function run(operation: () => Promise<void>): Promise<void> {
    busy = true;
    error = "";
    try {
      await operation();
    } catch (caught) {
      error =
        caught instanceof Error
          ? caught.message
          : "The atlas could not complete that action.";
    } finally {
      busy = false;
    }
  }

  function updatePreferences(next: Preferences): void {
    preferences = next;
    persistPreferences(next);
  }

  function connectRoomEvents(code: string): void {
    if (import.meta.env.VITE_API_MODE === "demo") return;
    roomEvents.connect(code, {
      onStatus: (status) => (relayConnection = status),
      onEvent: () => {
        void rooms.get(code).then((latest) => (room = latest));
      },
    });
  }

  function confirmExit(): void {
    if (session?.status === "active") {
      clearActiveSession(session.mode);
      session = { ...session, status: "abandoned" };
    }
    exitOpen = false;
    router.confirmPending();
  }

  function stayInGame(): void {
    exitOpen = false;
    router.dismissPending();
  }

  async function reportCurrent(): Promise<void> {
    if (!session) return;
    await api.reportContent({
      session_id: session.id,
      entity_qid: session.current.qid,
      reason: "unclear",
    });
    drawer = null;
    showToast("Report recorded for review.");
  }

  function showToast(message: string): void {
    toast = message;
    window.setTimeout(() => (toast = ""), 2800);
  }

  async function shareResult(): Promise<void> {
    if (!session) return;
    const marks = session.trail
      .map((item) => (item.revisited ? "↶" : "·"))
      .join("");
    const score =
      session.score === null ? "unranked" : `${session.score} points`;
    const text = `Webwoven ${session.mode === "daily" ? "Daily" : "Route"}\n${session.moves} moves · ${score}\n${marks}`;
    await navigator.clipboard?.writeText(text);
    showToast("Spoiler-free result copied.");
  }
</script>

<a class="skip-link" href="#page-content">Skip to content</a>
<div class="app-shell">
  <SiteHeader
    compact={route.name !== "home"}
    onHome={() => navigate("/")}
    onSources={() => (drawer = "sources")}
    onSettings={() => (drawer = "settings")}
  />

  <div id="page-content">
    {#if route.name === "home"}
      <LandingPage
        onSolo={() => begin("solo")}
        onDaily={() => begin("daily")}
        onRelay={() => navigate("/relay")}
      />
    {:else if route.name === "solo" || route.name === "daily" || route.name === "race"}
      {#if session}
        <GamePage
          {session}
          room={route.name === "race" ? room : undefined}
          {relayConnection}
          {busy}
          onFollow={(token) => void follow(token)}
          onBack={() => void back()}
          onHint={(type, propertyId) => void useHint(type, propertyId)}
        />
      {:else}
        <main class="loading-page">
          <span></span>
          <p>Unfolding the atlas…</p>
        </main>
      {/if}
    {:else if route.name === "lobby"}
      <LobbyPage
        {room}
        {busy}
        onCreate={() => void createRoom()}
        onJoin={(code) => void joinRoom(code)}
        onReady={() => void toggleReady()}
        onStart={() => void startRelay()}
      />
    {:else if route.name === "results" && session}
      <ResultsPage
        {session}
        {leaderboard}
        onAgain={() => begin("solo")}
        onDaily={() => begin("daily")}
        onHome={() => navigate("/")}
        onShare={() => void shareResult()}
      />
    {:else if route.name === "lab"}
      <LabPage />
    {:else}
      <NotFoundPage onHome={() => navigate("/")} />
    {/if}
  </div>

  {#if error}<div class="error-banner" role="alert">
      {error}<button type="button" onclick={() => (error = "")}>Dismiss</button>
    </div>{/if}
  <SettingsDrawer
    open={drawer === "settings"}
    {preferences}
    onChange={updatePreferences}
    onClose={() => (drawer = null)}
  />
  <SourcesDrawer
    open={drawer === "sources"}
    entity={session?.current}
    {graphBuild}
    onClose={() => (drawer = null)}
    onReport={() => void reportCurrent()}
  />
  <ExitDialog open={exitOpen} onStay={stayInGame} onLeave={confirmExit} />
  <StatusToast message={toast} />
</div>
