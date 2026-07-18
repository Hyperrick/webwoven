<script lang="ts">
  import type { Guest, RoomInvitePreview } from "../api/types";
  import ExitDialog from "./ExitDialog.svelte";
  import GuestNamePrompt from "./GuestNamePrompt.svelte";
  import LobbyInviteDialog from "./LobbyInviteDialog.svelte";
  import RouteConfetti from "./RouteConfetti.svelte";
  import StatusToast from "./StatusToast.svelte";

  let {
    exitOpen,
    namePromptOpen,
    guest,
    nameContext,
    profileBusy,
    inviteBusy,
    profileError,
    toast,
    celebrationSessionId,
    invite,
    onStay,
    onLeave,
    onNameSave,
    onNameKeep,
    onNameCancel,
    onInviteJoin,
    onInviteCancel,
  }: {
    exitOpen: boolean;
    namePromptOpen: boolean;
    guest?: Guest;
    nameContext: "daily" | "relay";
    profileBusy: boolean;
    inviteBusy: boolean;
    profileError: string;
    toast: string;
    celebrationSessionId?: string;
    invite?: RoomInvitePreview;
    onStay: () => void;
    onLeave: () => void;
    onNameSave: (name: string) => void;
    onNameKeep: () => void;
    onNameCancel: () => void;
    onInviteJoin: () => void;
    onInviteCancel: () => void;
  } = $props();
</script>

<ExitDialog open={exitOpen} {onStay} {onLeave} />
<GuestNamePrompt
  open={namePromptOpen}
  {guest}
  context={nameContext}
  busy={profileBusy}
  error={profileError}
  onSave={onNameSave}
  onKeep={onNameKeep}
  onCancel={onNameCancel}
/>
<LobbyInviteDialog
  {invite}
  busy={inviteBusy}
  onJoin={onInviteJoin}
  onCancel={onInviteCancel}
/>
<StatusToast message={toast} />
<RouteConfetti sessionId={celebrationSessionId} />
