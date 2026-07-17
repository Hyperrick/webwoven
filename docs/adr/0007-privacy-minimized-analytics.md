# ADR 0007: Privacy-minimized product analytics

## Status

Accepted on 2026-07-17.

## Context

Webwoven needs lightweight evidence about whether visitors start and finish rounds, which modes are
used, and whether hints help. Advertising analytics, persistent identifiers, session replay, and
free-form event payloads would be disproportionate to that goal.

## Decision

Run a pinned, self-hosted Umami instance and PostgreSQL database in the production Compose stack.
Serve it first-party from `stats.webwoven.org`; keep its dashboard behind Umami authentication; and
disable Umami telemetry, update calls, sharing, heatmaps, and session replay. The browser does not
load analytics when Do Not Track is enabled and excludes URL queries and hashes.

The client analytics adapter owns one allowlisted contract. It may send page views plus five events:
mode selected, round started, round completed, hint used, and route abandoned. Event values are
limited to reviewed enums and coarse buckets. Names, guest/session/entity identifiers, free-form
text, route histories, scores, and elapsed times are not part of the contract.

Detailed analytics expire after 90 days. Backups remain private, mode 600 server artifacts and use
the existing 14-day operational retention.

## Consequences

Webwoven gets a small conversion and gameplay dashboard without tracking cookies or third-party data
transfer. The deployment gains two containers, one private volume, one DNS name, one additional
backup, and a retention job. Analytics availability never gates gameplay: the client queues only a
small in-memory event set while the script loads and otherwise fails silently.
