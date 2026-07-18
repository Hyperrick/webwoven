# State machines

## Session

```text
active ──► completed
   ├─────► abandoned
   └─────► expired
```

A session command includes a unique client command ID and expected state version. Duplicate IDs
return their original result. Stale versions return the current snapshot without applying the
command. An active session may be scheduled but not yet playable: commands received before its
absolute `started_at` boundary return `round_not_started`. The browser introduction is a projection
of that timestamp, not an additional server state. An unfinished multiplayer session transitions to
`expired` at its Lobby's grace deadline so a late participant cannot remain in an active session
after the race has ended.

## Room

```text
lobby ──► countdown ──► racing ──► grace_period ──► finished
  │            ▲                                      │    │
  │            └──────── at least 2 yes votes ────────┘    │
  └──────────────────── close ─────────────────────────────► closed
                     fewer than 2 yes votes ───────────────►
```

The countdown and every participant session use the same absolute start time. Command
authorization reads that deadline directly: once it has passed, the first command may advance a
persisted `countdown` room to `racing` without waiting for a prior HTTP refresh or WebSocket event.
Commands remain open throughout `racing` and strictly before `grace_ends_at` in `grace_period`.

The first completed participant changes `racing` to `grace_period` and owns one 30-second deadline.
If everybody finishes earlier, or when that deadline expires, the room opens a 30-second rematch
vote in `finished`. The server expires every unfinished session at the grace deadline before
rejecting its next command. The WebSocket loop wakes at room transition deadlines so countdown,
grace, and rematch changes do not depend on arbitrary polling intervals.

The rematch vote resolves when all active participants have voted or `rematch_ends_at` passes. At
least two yes votes create new participant sessions and return the same room code to `countdown`;
only yes-voters remain active, and host ownership transfers to an accepted participant if needed.
With fewer than two yes votes the room enters `closed` with reason `not_enough_players`, and every
participant becomes inactive.

Connection, ready, active membership, and rematch vote are participant properties rather than
room-state variants. Reconnect replays retained events after the client's sequence number or sends
a full snapshot.
