<script lang="ts">
  import { onMount } from "svelte";
  import type { RelayConnectionState } from "./lib/api/room-event-stream";
  import { createRuntimeApi } from "./lib/api/runtime-api";
  import type {
    DailyLeaderboard,
    Guest,
    HintType,
    RoundFilters,
    RoomInvitePreview,
    RoomSnapshot,
    SessionSnapshot,
  } from "./lib/api/types";
  import { trackAnalytics } from "./lib/analytics/analytics";
  import { RoundLifecycleAnalytics } from "./lib/analytics/round-lifecycle-analytics";
  import AppDialogs from "./lib/components/AppDialogs.svelte";
  import AppDrawers from "./lib/components/AppDrawers.svelte";
  import SiteHeader from "./lib/components/SiteHeader.svelte";
  import { GameController } from "./lib/controllers/game-controller";
  import { RoomController } from "./lib/controllers/room-controller";
  import { confirmGuestName } from "./lib/guest-profile/guest-name";
  import {
    BrowserRouter,
    parseRoute,
    type AppRoute,
  } from "./lib/navigation/router";
  import {
    isProtectedGame,
    keepsRelayConnection,
    routeRequiresGuestName,
  } from "./lib/navigation/route-guards";
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
  import { RelayRuntime } from "./lib/relay/relay-runtime";
  import GamePage from "./lib/pages/GamePage.svelte";
  import LabPage from "./lib/pages/LabPage.svelte";
  import LandingPage from "./lib/pages/LandingPage.svelte";
  import LobbyPage from "./lib/pages/LobbyPage.svelte";
  import NotFoundPage from "./lib/pages/NotFoundPage.svelte";
  import ResultsPage from "./lib/pages/ResultsPage.svelte";
  import RoundSetupPage from "./lib/pages/RoundSetupPage.svelte";
  import PrivacyPage from "./lib/pages/PrivacyPage.svelte";

  const api = createRuntimeApi();
  const games = new GameController(api);
  const rooms = new RoomController(api);
  const roundAnalytics = new RoundLifecycleAnalytics();

  let route = $state<AppRoute>(parseRoute(window.location.pathname));
  let guest = $state<Guest>();
  let session = $state<SessionSnapshot>();
  let room = $state<RoomSnapshot>();
  let invite = $state<RoomInvitePreview>();
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
  let celebrationSessionId = $state<string>();
  let exitOpen = $state(false);
  let graphBuild = $state("loading-atlas");
  let relayConnection = $state<RelayConnectionState>("connected");
  let namePromptOpen = $state(false);
  let profileBusy = $state(false);
  let profileError = $state("");
  let router: BrowserRouter;
  const currentRoom = () => room;
  const relay = new RelayRuntime(rooms, games, {
    route: () => route,
    session: () => session,
    setRoom: (latest) => (room = latest),
    setSession: (latest) => (session = latest),
    setConnection: (status) => (relayConnection = status),
    reportStarted: (latest) => roundAnalytics.reportStarted(latest),
    navigate: (path) => navigate(path, true),
    reportError: (message) => (error = message),
  });

  onMount(() => {
    preferences = loadPreferences();
    persistPreferences(preferences);
    router = new BrowserRouter({
      isProtected: () => isProtectedGame(session, route),
      onRoute: (next) => {
        if (!keepsRelayConnection(next)) relay.stop();
        route = next;
        void hydrateRoute(next);
      },
      onBlockedNavigation: () => (exitOpen = true),
    });
    const stop = router.start();
    void run(initialize);
    return () => {
      stop();
      relay.stop();
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
    if (routeRequiresGuestName(guest, next)) {
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
    if (next.name === "lobby-invite") {
      await run(async () => {
        room = undefined;
        invite = await rooms.invite(next.code);
      });
      return;
    }
    if (next.name === "race" && (!room || room.code !== next.code)) {
      await run(async () => relay.hydrate(next.code));
    }
    if (next.name === "relay-results" && (!room || room.code !== next.code)) {
      await run(async () => relay.hydrate(next.code, false));
    }
    if (
      next.name === "results" &&
      session?.mode === "daily" &&
      leaderboardStatus === "idle"
    ) {
      void loadDailyLeaderboard();
    }
  }

  function navigate(path: string, bypassGuard = false, replace = false): void {
    router?.navigate(path, { bypassGuard, replace });
  }

  function begin(mode: "solo" | "daily"): void {
    trackAnalytics("mode_selected", { mode });
    clearActiveSession(mode);
    session = undefined;
    if (mode === "daily") resetLeaderboard();
    navigate(`/play/${mode}`);
  }

  function beginRelay(): void {
    trackAnalytics("mode_selected", { mode: "relay" });
    relay.stop();
    room = undefined;
    invite = undefined;
    session = undefined;
    navigate("/lobby");
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
      session = await games.start("daily", { roundId: round.round_id });
      session = { ...session, shortest_distance: round.optimal_distance };
      persistActiveSession(session);
      roundAnalytics.reportStarted(session);
    });
  }

  async function confirmSolo(filters: RoundFilters): Promise<void> {
    await run(async () => {
      session = await games.start("solo", filters);
      persistActiveSession(session);
      roundAnalytics.reportStarted(session);
    });
  }

  async function follow(edgeToken: string): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await relay.follow(session!, edgeToken, currentRoom);
      persistActiveSession(session);
      if (session.status === "completed") {
        celebrationSessionId = session.id;
        roundAnalytics.reportCompleted(session);
        if (session.mode === "daily") void loadDailyLeaderboard();
        await relay.navigateAfterCompletion(session, room);
      }
    });
  }

  async function back(): Promise<void> {
    if (!session) return;
    await run(async () => {
      session = await relay.back(session!, currentRoom);
      persistActiveSession(session);
    });
  }

  async function useHint(
    type: HintType,
    property?: string,
    entity?: string,
  ): Promise<void> {
    if (!session) return;
    await run(async () => {
      const previousHintCount = session!.hints_used.length;
      session = await relay.hint(session!, type, currentRoom, property, entity);
      persistActiveSession(session);
      if (session.hints_used.length > previousHintCount) {
        trackAnalytics("hint_used", {
          mode: session.mode,
          difficulty: session.difficulty,
          category: session.category,
          hint: type,
        });
      }
    });
  }

  async function createRoom(filters: RoundFilters): Promise<void> {
    await run(async () => {
      room = await rooms.create(filters);
      relay.connect(room.code);
    });
  }

  async function joinRoom(code: string): Promise<void> {
    await run(async () => {
      room = await rooms.join(code);
      relay.connect(room.code);
    });
  }

  async function openInvite(): Promise<void> {
    if (!invite) return;
    await run(async () => {
      const latest = invite!.is_member
        ? await rooms.get(invite!.code)
        : await rooms.join(invite!.code);
      invite = undefined;
      room = latest;
      relay.connect(latest.code);
      if (latest.state === "lobby") {
        navigate("/lobby", true, true);
        return;
      }
      if (!latest.current_session_id)
        throw new Error("This lobby no longer has a route for you.");
      session = await games.resume(latest.current_session_id);
      const resultState =
        latest.state === "finished" || latest.state === "closed";
      const resultPath = `/lobby/${latest.code}/results`;
      navigate(
        resultState || session.status !== "active"
          ? resultPath
          : `/lobby/${latest.code}`,
        true,
        true,
      );
    });
  }

  function cancelInvite(): void {
    invite = undefined;
    navigate("/", true, true);
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
      navigate(`/lobby/${room.code}`);
      if (!room.current_session_id)
        throw new Error("The lobby did not assign your synchronized route.");
      session = await games.resume(room.current_session_id);
      roundAnalytics.reportStarted(session);
      relay.connect(room.code);
    });
  }

  async function voteRematch(accept: boolean): Promise<void> {
    if (!room) return;
    await run(async () => {
      const latest = await rooms.voteRematch(room!, accept);
      await relay.apply(latest);
    });
  }

  async function refreshRelay(): Promise<void> {
    if (!room) return;
    await run(async () => relay.apply(await rooms.get(room!.code)));
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

  function confirmExit(): void {
    if (session?.status === "active") {
      trackAnalytics("route_abandoned", {
        mode: session.mode,
        difficulty: session.difficulty,
        category: session.category,
        progress: session.moves === 0 ? "no_moves" : "in_progress",
      });
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
    {:else if route.name === "lobby" || route.name === "lobby-invite"}
      <LobbyPage
        {room}
        {busy}
        onCreate={(filters) => void createRoom(filters)}
        onJoin={(code) => void joinRoom(code)}
        onReady={() => void toggleReady()}
        onStart={() => void startRelay()}
      />
    {:else if (route.name === "results" || route.name === "relay-results") && session}
      <ResultsPage
        {session}
        {leaderboard}
        {leaderboardStatus}
        {leaderboardError}
        room={route.name === "relay-results" ? room : undefined}
        relayBusy={busy}
        onLeaderboardRetry={() => void loadDailyLeaderboard()}
        onSolo={() => begin("solo")}
        onDaily={() => begin("daily")}
        onRelay={beginRelay}
        onRelayVote={(accept) => void voteRematch(accept)}
        onRelayRefresh={() => void refreshRelay()}
        onHome={() => navigate("/")}
      />
    {:else if route.name === "lab"}
      <LabPage />
    {:else if route.name === "privacy"}
      <PrivacyPage />
    {:else}
      <NotFoundPage onHome={() => navigate("/")} />
    {/if}
  </div>

  {#if error}<div class="error-banner" role="alert" inert={drawer !== null}>
      {error}<button type="button" onclick={() => (error = "")}>Dismiss</button>
    </div>{/if}
  <AppDrawers
    open={drawer}
    {guest}
    {preferences}
    nameBusy={profileBusy}
    nameError={profileError}
    nameDisabled={["lobby", "lobby-invite", "race", "relay-results"].includes(
      route.name,
    )}
    {leaderboard}
    {leaderboardStatus}
    {leaderboardError}
    {session}
    {graphBuild}
    onPreferencesChange={updatePreferences}
    onNameSave={(name) => void saveSettingsName(name)}
    onLeaderboardRetry={() => void loadDailyLeaderboard()}
    onReport={() => void reportCurrent()}
    onClose={() => (drawer = null)}
  />
  <AppDialogs
    {exitOpen}
    {namePromptOpen}
    {guest}
    nameContext={route.name === "daily" ? "daily" : "relay"}
    {profileBusy}
    inviteBusy={busy}
    {profileError}
    {toast}
    {celebrationSessionId}
    {invite}
    onStay={stayInGame}
    onLeave={confirmExit}
    onNameSave={(name) => void savePromptName(name)}
    onNameKeep={keepGeneratedName}
    onNameCancel={cancelNamePrompt}
    onInviteJoin={() => void openInvite()}
    onInviteCancel={cancelInvite}
  />
</div>
