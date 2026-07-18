# OpenAI Build Week Devpost draft

This is the copy-ready submission package. It was prepared against the official OpenAI Build Week
rules and FAQ on July 18, 2026. It is a draft, not proof that the project has been submitted.

## Project overview

**Project name:** Webwoven

**Tagline:** A knowledge game where every move explains why two things are connected.

**Track:** Education

**Submitter type:** Individual, entrant eligibility confirmed

**Country:** Germany

**Saved Devpost draft:** [https://devpost.com/software/webwoven](https://devpost.com/software/webwoven)

**Project status:** A detailed concept brief existed before the challenge; the working application
and repository implementation were created during the submission period.

**Try it out:** [https://www.webwoven.org](https://www.webwoven.org)

**Repository:** [https://github.com/Hyperrick/webwoven](https://github.com/Hyperrick/webwoven)

**License:** MIT for project-authored source and documentation. Wikidata data is CC0; Wikimedia
Commons assets retain their recorded licenses and attribution.

**Demo video:** [https://youtu.be/TzIuJh-kdGc](https://youtu.be/TzIuJh-kdGc)

**Primary Codex Session ID:** `019f5c2a-d9b1-7e11-b671-5868c93b8241`

**Thumbnail:** `docs/assets/submission/devpost-thumbnail.png`

**YouTube thumbnail:** `docs/assets/submission/youtube-thumbnail.png`

**Gallery:** `docs/assets/submission/frontispiece.png` and
`docs/assets/submission/mobile-route-preview.png`

## Project story

### Inspiration

Most knowledge games test whether you already know an isolated fact. I wanted a game that makes the
connections themselves visible: not just that George Orwell and Beyoncé can be linked, but the
named, sourced relationships that form the route between them.

Webwoven began as a detailed game concept and a larger personal question: can one person with a
clear idea use Codex to become a game developer in a week? The answer had to be a real product, not
a prototype screenshot or an AI chat wrapped in a game skin.

### What it does

Webwoven is a competitive, explainable knowledge-graph game built from Wikidata. A round gives you
a start and a target. Every move follows a real relationship and says why the two entities are
connected. The map grows as you play, preserving the path, discarded branches, sources, licensed
documentary images, and the facts behind each choice.

There are three complete ways to play:

- **Single player** lets you choose a difficulty and optionally focus the endpoints on one of ten
  knowledge topics.
- **Daily challenge** gives everyone the same connection and a shared leaderboard.
- **Multiplayer** synchronizes a route for two to four players, including live progress and
  reconnect.

The production atlas contains 3,970 playable entities, 22,402 directed named relationships, 100
validated candidates, and 40 published routes. It works on desktop and mobile, needs no account,
and is live at [www.webwoven.org](https://www.webwoven.org).

### How I built it

The original concept brief and product direction were mine. The primary implementation task ran on
**GPT-5.6 Sol in Codex**. Codex translated the brief into a modular Svelte 5 client, a
server-authoritative FastAPI application, a versioned Python knowledge pipeline, production
operations, tests, and public documentation. Specialized parallel Codex tasks worked on the web,
API, data, persistence, security, and review surfaces against shared contracts, then the combined
product went through one quality gate.

Codex accelerated the breadth of the build: while the pipeline normalized Wikidata statements and
Commons licenses, the game domains could implement navigation, scoring, hints, Daily, and
Multiplayer. I steered the decisions that make those pieces one product: named connections instead
of opaque links, a deterministic and server-authoritative runtime, a strict editorial-atlas design
system, source inspection on every move, privacy-minimized analytics, and no AI call during
gameplay.

GPT-5.6 was also used iteratively rather than only for scaffolding. Hands-on desktop and phone
playtests exposed unclear play modes, cyclic routes, dense maps, ambiguous relationship wording,
and touch interactions that looked correct but felt wrong. I fed those observations back into
Codex; it traced each issue to its owning domain, implemented focused changes, added regression
coverage, rebuilt the real Compose surface, and rechecked the result.

The AI boundary is deliberate. GPT-5.6 and Codex built the product and can create reviewed,
provenance-labelled build artifacts. They do not choose a player's legal moves, hints, score,
route, or winner. Runtime gameplay makes no request to Wikidata, Wikimedia, Wikipedia, or an AI
service; it uses one immutable, checksum-verified local atlas.

### Challenges

The hardest part was turning a huge public graph into a readable game. Real entities can have
dozens of neighbors, inverse facts can create trivial loops, and a technically correct statement
can still sound false when rendered in the wrong direction. Webwoven solves that with a
deterministic six-destination frontier, cycle-free active routes with explicit Back behavior,
source-neutral relationship semantics, and automated publication checks for every round.

The second challenge was making one graph feel native on both a wide desktop and a narrow phone.
Desktop uses a left-to-right atlas with a compact utility rail. Phones project the same state into
a top-to-bottom two-column constellation with preview-then-confirm touch behavior. Both layouts
consume the same domain projection and server commands.

The final challenge was provenance. Every published image has a source, creator, license, URL,
retrieval record, and content hash. Every Codex-assisted content artifact has a prompt, fact hash,
output hash, validation result, approval state, and truthful generator label.

### Accomplishments I am proud of

- A completely open-source, production-like game was built and deployed during Build Week.
- Single player, Daily, and synchronized Multiplayer are all real, tested modes rather than demo
  toggles.
- The complete production loop works without an AI key or runtime AI dependency.
- The current gate covers 139 web tests, 348 Python tests, and 32 desktop/mobile Playwright flows,
  plus formatting, linting, type checks, strict docs, data validation, and container builds.
- The public build journal records product decisions, failed approaches, data provenance, and the
  line between Codex acceleration and human approval.

### What I learned

Codex is strongest when it is given ownership boundaries and evidence, not just a feature list.
Small domain contracts let parallel tasks move quickly without duplicating game rules. Real browser
and production checks then turn plausible code into a coherent product.

I also learned that explainability can be gameplay. Showing the relationship sentence, source,
image, and route history does not have to feel like documentation; it can be the thing that makes
each move surprising and memorable.

### What's next

Next I would expand the reviewed route pool, add optional private accounts for cross-device history,
and build classroom-friendly shared expeditions where a teacher can pin a topic without changing
the source-backed game rules. The immediate goal is simpler: watch new players, identify where the
first round still needs explanation, and keep improving the completely open-source game in public.

## Built with tags

Codex, GPT-5.6, Svelte, TypeScript, Three.js, FastAPI, Python, SQLite, PostgreSQL, Valkey, Wikidata,
Wikimedia Commons, Docker Compose, Caddy, Playwright, MkDocs, Umami

## Judge testing instructions

The fastest path requires no account, install, or test data:

1. Open [https://www.webwoven.org](https://www.webwoven.org).
2. Choose **Single player**, leave **Any category** selected, and start an Easy route.
3. Follow a named connection and inspect its complete fact and source without moving.
4. Use **Fit map** to see the preserved route and discarded branches.
5. Return home and open **Daily challenge** to see the shared round and leaderboard.
6. For Multiplayer, create a room and open its join URL in a second browser or private window.

The live instance is free and needs no credentials. The public repository contains full setup,
testing, data-build, architecture, and deployment instructions. Building the complete Wikidata and
Commons pack is intentionally separate from the credential-free smoke fixture; judges can evaluate
the real pack immediately on the live instance without rebuilding it.

## Demo video script and shot list

The plain-English TTS script is in [`demo-voiceover.txt`](demo-voiceover.txt). The matching
[production plan](demo-video.md) records the measured narration timing, final Remotion storyboard,
caption checks, and visual safety rules. The published 2:31 narrated video is available at
[https://youtu.be/TzIuJh-kdGc](https://youtu.be/TzIuJh-kdGc), safely below the three-minute limit.

## Final form checklist

- [x] Confirm individual entrant details, Germany, and country eligibility.
- [ ] Recheck the official rules and any Devpost form changes on submission day.
- [x] Run `/feedback` in the primary **Implement Webwoven game** task and save the returned Session
      ID in the form.
- [x] Record and publish the narrated demo with GPT-5.6/Codex evidence.
- [x] Save the overview, Education track, story, built-with tags, live URL, repository URL, YouTube
      URL, judge instructions, and feedback ID in the Devpost draft.
- [x] Verify the public repository, live product, and embedded public YouTube video.
- [x] Preview the saved draft on desktop and at 412x915; the copy and links render, while Devpost's
      narrow layout clips the embedded YouTube player horizontally.
- [ ] Upload the 3:2 thumbnail and two gallery images after Chrome file access is available.
- [ ] Review third-party media and complete the final rights and terms declarations.
- [ ] Recheck the completed page on desktop and mobile after media upload.
- [ ] Submit before the internal July 21, 22:00 CEST freeze.
