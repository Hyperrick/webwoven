<script lang="ts">
  import { onMount } from "svelte";
  import {
    RoomEventStream,
    type RelayConnectionState,
  } from "./lib/api/room-event-stream";
  import { createRuntimeApi } from "./lib/api/runtime-api";
  import type {
    DailyLeaderboard,
    Difficulty,
    Guest,
    HintType,
    RoomSnapshot,
    SessionSnapshot,
  } from "./lib/api/types";
  import DailyLeaderboardDrawer from "./lib/components/DailyLeaderboardDrawer.svelte";
  import GuestNamePrompt from "./lib/components/GuestNamePrompt.svelte";
  import SettingsDrawer from "./lib/components/SettingsDrawer.svelte";
  import SiteHeader from "./lib/components/SiteHeader.svelte";
  import SourcesDrawer from "./lib/components/SourcesDrawer.svelte";
  import ExitDialog from "./lib/components/ExitDialog.svelte";
  import StatusToast from "./lib/components/StatusToast.svelte";
  import { GameController } from "./lib/controllers/game-controller";
  import { RoomController } from "./lib/controllers/room-controller";
  import { sessionMediaEntities } from "./lib/domain/trail-entities";
  import {
    confirmGuestName,
    isGuestNameConfirmed,
  } from "./lib/guest-profile/guest-name";
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
  import RoundSetupPage from "./lib/pages/RoundSetupPage.svelte";

  const api = createRuntimeApi();
  const games = new GameController(api);
  const rooms = new RoomController(api);
  const roomEvents = new RoomEventStream();

  let route = $state<AppRoute>(parseRoute(window.location.pathname));
  let guest = $state<Guest>();
  let session = $state<SessionSnapshot>();
  let room = $state<RoomSnapshot>();
  let leaderboard = $state<DailyLeaderboard>({
    entries: [],
    current_guest_entry: null,
  });
  let leaderboardStatus = $state<"idle" | "loading" | "ready" | "error">(
    "idle",
  );
  let leaderboardError = $state("");
  let preferences = $state<Preferences>(DEFAULT_PREFERENCES);
  let drawer = $state<"leaderboard" | "settings" | "sources" | null>(null);
  let busy = $state(false);
  let error = $state("");
  let toast = $state("");
  let exitOpen = $state(false);
  let graphBuild = $state("loading-atlas");
  let relayConnection = $state<RelayConnectionState>("connected");
  let namePromptOpen = $state(false);
  let profileBusy = $state(false);
  let profileError = $state("");
  let router: BrowserRouter;
  let sourceEntities = $derived(session ? sessionMediaEntities(session) : []);

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
      guest = await api.getGuest();
    } catch {
      guest = await api.createGuest();
    }
    const config = await api.getConfig();
    graphBuild = config.graph_build;
    await hydrateRoute(route);
  }

  async function hydrateRoute(next: AppRoute): Promise<void> {
    if (requiresGuestName(next)) {
      namePromptOpen = true;
      return;
    }
    namePromptOpen = false;
    if (next.name === "solo" && !session) {
      await restoreSession("solo");
    }
    if (next.name === "daily" && !session) {
      await restoreOrStartDaily();
    }
    if (next.name === "race" && (!room || room.code !== next.code)) {
      await run(async () => {
        room = await rooms.join(next.code);
        if (!room.current_session_id)
          throw new Error("This relay has not assigned your route yet.");
        session = await games.resume(room.current_session_id);
        connectRoomEvents(room.code);
      });
    }
    if (
      next.name === "results" &&
      session?.mode === "daily" &&
      leaderboardStatus === "idle"
    ) {
      void loadDailyLeaderboard();
    }
  }

  function requiresGuestName(next: AppRoute): boolean {
    return Boolean(
      guest &&
      ["daily", "lobby", "race"].includes(next.name) &&
      !isGuestNameConfirmed(guest),
    );
  }

  function navigate(path: string, bypassGuard = false): void {
    router?.navigate(path, { bypassGuard });
  }

  function begin(mode: "solo" | "daily"): void {
    clearActiveSession(mode);
    session = undefined;
    if (mode === "daily") resetLeaderboard();
    navigate(`/play/${mode}`);
  }

  function beginRelay(): void {
    roomEvents.stop();
    room = undefined;
    session = undefined;
    navigate("/relay");
  }

  async function restoreSession(mode: "solo" | "daily"): Promise<boolean> {
    let restored = false;
    await run(async () => {
      const storedId = loadActiveSessionId(mode);
      if (storedId) {
        try {
          const snapshot = await games.resume(storedId);
          if (snapshot.mode === mode && snapshot.status === "active") {
            session = snapshot;
            persistActiveSession(snapshot);
            restored = true;
            return;
          }
        } catch {
          // A removed or graph-incompatible session starts cleanly below.
        }
        clearActiveSession(mode);
      }
    });
    return restored;
  }

  async function restoreOrStartDaily(): Promise<void> {
    if (await restoreSession("daily")) return;
    await run(async () => {
      const round = await api.getDaily();
      session = await games.start("daily", round.round_id);
      session = { ...session, shortest_distance: round.optimal_distance };
      persistActiveSession(session);
    });
  }

  async function confirmSolo(difficulty: Difficulty): Promise<void> {
    await run(async () => {
      session = await games.start("solo", undefined, difficulty);
      persistActiveSession(session);
    });
  }

  async function follow(edgeToken: string): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await games.follow(session!, edgeToken);
      persistActiveSession(session);
      if (session.status === "completed") {
        if (session.mode === "daily") void loadDailyLeaderboard();
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

  async function useHint(
    type: HintType,
    propertyId?: string,
    entityQid?: string,
  ): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await games.hint(session!, type, propertyId, entityQid);
      persistActiveSession(session);
    });
  }

  async function createRoom(difficulty: Difficulty): Promise<void> {
    await run(async () => {
      room = await rooms.create(difficulty);
      connectRoomEvents(room.code);
    });
  }

  async function joinRoom(code: string): Promise<void> {
    await run(async () => {
      room = await rooms.join(code);
      connectRoomEvents(room.code);
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
      if (!room.current_session_id)
        throw new Error("The relay did not assign your synchronized route.");
      session = await games.resume(room.current_session_id);
      connectRoomEvents(room.code);
    });
  }

  function resetLeaderboard(): void {
    leaderboard = { entries: [], current_guest_entry: null };
    leaderboardStatus = "idle";
    leaderboardError = "";
  }

  async function loadDailyLeaderboard(): Promise<void> {
    leaderboardStatus = "loading";
    leaderboardError = "";
    try {
      leaderboard = await api.getDailyLeaderboard();
      leaderboardStatus = "ready";
    } catch (caught) {
      leaderboardStatus = "error";
      leaderboardError =
        caught instanceof Error
          ? caught.message
          : "Today’s field could not be loaded.";
    }
  }

  async function updateGuestName(name: string): Promise<boolean> {
    if (!guest) return false;
    profileBusy = true;
    profileError = "";
    try {
      guest = await api.updateGuest(name);
      confirmGuestName(guest);
      return true;
    } catch (caught) {
      profileError =
        caught instanceof Error
          ? caught.message
          : "The explorer name could not be saved.";
      return false;
    } finally {
      profileBusy = false;
    }
  }

  async function savePromptName(name: string): Promise<void> {
    if (!(await updateGuestName(name))) return;
    namePromptOpen = false;
    await hydrateRoute(route);
  }

  function keepGeneratedName(): void {
    if (!guest) return;
    confirmGuestName(guest);
    profileError = "";
    namePromptOpen = false;
    void hydrateRoute(route);
  }

  function cancelNamePrompt(): void {
    profileError = "";
    namePromptOpen = false;
    navigate("/", true);
  }

  async function saveSettingsName(name: string): Promise<void> {
    if (!(await updateGuestName(name))) return;
    showToast("Explorer name updated.");
    if (route.name === "results" && session?.mode === "daily")
      void loadDailyLeaderboard();
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

  function openSettings(): void {
    profileError = "";
    drawer = "settings";
  }

  function openDailyLeaderboard(): void {
    drawer = "leaderboard";
    void loadDailyLeaderboard();
  }

  function connectRoomEvents(code: string): void {
    if (import.meta.env.VITE_API_MODE === "demo") return;
    roomEvents.connect(code, {
      onStatus: (status) => (relayConnection = status),
      onEvent: () => {
        void refreshRoomFromEvent(code);
      },
    });
  }

  async function refreshRoomFromEvent(code: string): Promise<void> {
    const latest = await rooms.get(code);
    room = latest;
    if (
      route.name === "lobby" &&
      (latest.state === "countdown" || latest.state === "racing") &&
      latest.current_session_id
    ) {
      session = await games.resume(latest.current_session_id);
      navigate(`/relay/${latest.code}`);
    }
  }

  function confirmExit(): void {
    if (session?.status === "active") {
      if (session.mode !== "relay") clearActiveSession(session.mode);
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
</script>

<a class="skip-link" href="#page-content" inert={drawer !== null}
  >Skip to content</a
>
<div class="app-shell">
  <SiteHeader
    compact={route.name !== "home"}
    leaderboardOpen={drawer === "leaderboard"}
    pageInert={drawer !== null}
    onHome={() => navigate("/")}
    onLeaderboard={openDailyLeaderboard}
    onSources={() => (drawer = "sources")}
    onSettings={openSettings}
  />

  <div id="page-content" inert={drawer !== null}>
    {#if route.name === "home"}
      <LandingPage
        onSolo={() => begin("solo")}
        onDaily={() => begin("daily")}
        onRelay={beginRelay}
      />
    {:else if route.name === "solo" && !session}
      <RoundSetupPage {busy} onConfirm={(value) => void confirmSolo(value)} />
    {:else if route.name === "solo" || route.name === "daily" || route.name === "race"}
      {#if session}
        <GamePage
          {session}
          room={route.name === "race" ? room : undefined}
          {relayConnection}
          {busy}
          onFollow={(token) => void follow(token)}
          onBack={() => void back()}
          onHint={(type, propertyId, entityQid) =>
            void useHint(type, propertyId, entityQid)}
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
        onCreate={(difficulty) => void createRoom(difficulty)}
        onJoin={(code) => void joinRoom(code)}
        onReady={() => void toggleReady()}
        onStart={() => void startRelay()}
      />
    {:else if route.name === "results" && session}
      <ResultsPage
        {session}
        {leaderboard}
        {leaderboardStatus}
        {leaderboardError}
        onLeaderboardRetry={() => void loadDailyLeaderboard()}
        onSolo={() => begin("solo")}
        onDaily={() => begin("daily")}
        onRelay={beginRelay}
        onHome={() => navigate("/")}
      />
    {:else if route.name === "lab"}
      <LabPage />
    {:else}
      <NotFoundPage onHome={() => navigate("/")} />
    {/if}
  </div>

  {#if error}<div class="error-banner" role="alert" inert={drawer !== null}>
      {error}<button type="button" onclick={() => (error = "")}>Dismiss</button>
    </div>{/if}
  <SettingsDrawer
    open={drawer === "settings"}
    {guest}
    {preferences}
    nameBusy={profileBusy}
    nameError={profileError}
    nameDisabled={route.name === "lobby" || route.name === "race"}
    onChange={updatePreferences}
    onNameSave={(name) => void saveSettingsName(name)}
    onClose={() => (drawer = null)}
  />
  <DailyLeaderboardDrawer
    open={drawer === "leaderboard"}
    {leaderboard}
    status={leaderboardStatus}
    error={leaderboardError}
    onRetry={() => void loadDailyLeaderboard()}
    onClose={() => (drawer = null)}
  />
  <SourcesDrawer
    open={drawer === "sources"}
    entity={session?.current}
    roundEntities={sourceEntities}
    {graphBuild}
    onClose={() => (drawer = null)}
    onReport={() => void reportCurrent()}
  />
  <ExitDialog open={exitOpen} onStay={stayInGame} onLeave={confirmExit} />
  <GuestNamePrompt
    open={namePromptOpen}
    {guest}
    context={route.name === "daily" ? "daily" : "relay"}
    busy={profileBusy}
    error={profileError}
    onSave={(name) => void savePromptName(name)}
    onKeep={keepGeneratedName}
    onCancel={cancelNamePrompt}
  />
  <StatusToast message={toast} />
</div>
