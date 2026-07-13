# State machines

## Session

```text
active ──► completed
   ├─────► abandoned
   └─────► expired
```

A session command includes a unique client command ID and expected state version. Duplicate IDs
return their original result. Stale versions return the current snapshot without applying the
command.

## Room

```text
lobby ──► countdown ──► racing ──► grace_period ──► finished ──► closed
  └────────────────────────────────────────────────────────────► closed
```

Connection and ready state are properties of a participant rather than room-state variants.
Reconnect replays retained events after the client's sequence number or sends a full snapshot.
