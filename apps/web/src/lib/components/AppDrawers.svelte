<script lang="ts">
  import type { DailyLeaderboard, Guest, SessionSnapshot } from "../api/types";
  import { sessionMediaEntities } from "../domain/trail-entities";
  import type { Preferences } from "../preferences/preferences";
  import DailyLeaderboardDrawer from "./DailyLeaderboardDrawer.svelte";
  import SettingsDrawer from "./SettingsDrawer.svelte";
  import SourcesDrawer from "./SourcesDrawer.svelte";

  let {
    open,
    guest,
    preferences,
    nameBusy,
    nameError,
    nameDisabled,
    leaderboard,
    leaderboardStatus,
    leaderboardError,
    session,
    graphBuild,
    onPreferencesChange,
    onNameSave,
    onLeaderboardRetry,
    onReport,
    onClose,
  }: {
    open: "leaderboard" | "settings" | "sources" | null;
    guest?: Guest;
    preferences: Preferences;
    nameBusy: boolean;
    nameError: string;
    nameDisabled: boolean;
    leaderboard: DailyLeaderboard;
    leaderboardStatus: "idle" | "loading" | "ready" | "error";
    leaderboardError: string;
    session?: SessionSnapshot;
    graphBuild: string;
    onPreferencesChange: (next: Preferences) => void;
    onNameSave: (name: string) => void;
    onLeaderboardRetry: () => void;
    onReport: () => void;
    onClose: () => void;
  } = $props();

  let sourceEntities = $derived(session ? sessionMediaEntities(session) : []);
</script>

<SettingsDrawer
  open={open === "settings"}
  {guest}
  {preferences}
  {nameBusy}
  {nameError}
  {nameDisabled}
  onChange={onPreferencesChange}
  {onNameSave}
  {onClose}
/>
<DailyLeaderboardDrawer
  open={open === "leaderboard"}
  {leaderboard}
  status={leaderboardStatus}
  error={leaderboardError}
  onRetry={onLeaderboardRetry}
  {onClose}
/>
<SourcesDrawer
  open={open === "sources"}
  entity={session?.current}
  roundEntities={sourceEntities}
  {graphBuild}
  {onClose}
  {onReport}
/>
