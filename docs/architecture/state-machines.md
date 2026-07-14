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
of that timestamp, not an additional server state.

## Room

```text
lobby ──► countdown ──► racing ──► grace_period ──► finished ──► closed
  └────────────────────────────────────────────────────────────► closed
```

Connection and ready state are properties of a participant rather than room-state variants.
Reconnect replays retained events after the client's sequence number or sends a full snapshot.
