# Demo video production plan

The exact narration is in [`demo-voiceover.txt`](demo-voiceover.txt). It uses short sentences and
plain words for TTS. The approved MP3 runs for 148.767313 seconds, and the final 151-second video
stays safely below the three-minute limit.

## Approved narration

- The approved audio is `apps/demo-video/public/audio/voiceover.mp3`.
- It uses a calm, clear English voice with short pauses between paragraphs and no music.
- Its measured duration is 148.767313 seconds.
- The corrected sidecar captions are `apps/demo-video/public/captions/voiceover.srt`.
- The SRT contains 35 sequential, non-overlapping cues and ends at 148.700 seconds.
- The final picture holds for 2.23 seconds after the narration ends.

The eight scene boundaries are aligned to the measured paragraph starts in the approved audio.
Silent renders remain available for picture-only review, but the Devpost delivery is the narrated
render. The public narrated delivery is
[https://youtu.be/TzIuJh-kdGc](https://youtu.be/TzIuJh-kdGc), with the upload artwork stored at
`docs/assets/submission/youtube-thumbnail.png`.

## Remotion-ready storyboard

| Scene             |    Final time | Narration   | Visual                                                                                                              |
| ----------------- | ------------: | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Hook              | 0:00.0–0:11.3 | Paragraph 1 | Start on the current real node map, then show the Webwoven name and current goal.                                   |
| Start a round     | 0:11.3–0:26.4 | Paragraph 2 | Show the current Single-player setup with difficulty and topic, then the round introduction.                        |
| Explainable moves | 0:26.4–0:50.1 | Paragraph 3 | Return to the node map, open the Rosario connection, and show the fact, picture, source, and hints.                 |
| Three modes       | 0:50.1–1:06.5 | Paragraph 4 | Readable cuts of the current Single-player start, Daily result board, and live two-player Multiplayer map.          |
| Codex and GPT-5.6 | 1:06.5–1:35.3 | Paragraph 5 | Name Codex and GPT-5.6 Sol, then show the architecture, focused source folders, tests, and human-directed workflow. |
| Iteration         | 1:35.3–1:57.2 | Paragraph 6 | Pair the current desktop and phone views with the four changes made after play testing.                             |
| Trust boundary    | 1:57.2–2:18.1 | Paragraph 7 | Return to the node map and show the checked local-atlas size, deterministic rules, and zero runtime AI calls.       |
| Close             | 2:18.1–2:31.0 | Paragraph 8 | End on the route result with the live URL and the line “Connect anything. Discover why it is connected.”            |

## Visual rules

- Use actual Webwoven footage and repository evidence, not generated UI mock-ups.
- Keep most cuts between three and eight seconds so the judge can read the screen.
- Use simple crossfades and gentle zooms; avoid flashy transitions.
- Put short captions only where they add proof: `3 play modes`, `GPT-5.6 Sol + Codex`,
  `3,970 entities`, `22,402 connections`, and `No runtime AI calls`.
- Never show secrets, private transcript text, hidden reasoning, local environment values, or
  unrelated browser tabs.
- Do not add decorative third-party logos, unlicensed promotional media, or copyrighted music.
  Real gameplay footage may retain the source-backed entity names and documentary media recorded
  in the attribution ledger; the entrant must complete the final rights review before submission.

## Implemented Remotion workflow

The production project now lives in `apps/demo-video`. It defines two 1920×1080, 30 fps
compositions:

- `WebwovenDemo`: the 2:31 Build Week edit, matching the eight final storyboard scenes above. It
  contains 4,530 frames at 30 fps.
- `WebwovenTeaser`: a 24-second review cut that opens on the node map, shows real gameplay, and
  closes on the product line.

All product visuals come from the rebuilt Compose acceptance surface at `http://localhost`. The
current gameplay capture is a real 1920×1080 Solo route from Lionel Messi through Rosario,
Argentina, UNESCO, and France to Tour de France. It is stored for Remotion as
`apps/demo-video/public/captures/current-gameplay.mp4`; the current setup, Daily result, live
Multiplayer, mobile, and node-map stills are under `apps/demo-video/public/images/`.

To refresh the canonical product bundle and record the same capture surface:

```bash
docker compose build caddy
docker compose up -d caddy
CAPTURE_NAME=webwoven-current-1080 CAPTURE_WIDTH=1920 CAPTURE_HEIGHT=1080 \
  node output/playwright/linkedin-gif/record-linkedin-sqlite.mjs
```

Use Remotion Studio for timing and layout review:

```bash
pnpm --filter @webwoven/demo-video dev
```

Render the lightweight review files before the final full-resolution encode:

```bash
pnpm --filter @webwoven/demo-video render:teaser:quick
pnpm --filter @webwoven/demo-video render:demo:quick
pnpm --filter @webwoven/demo-video render:demo:narrated:quick
```

These write `output/webwoven-teaser-preview.mp4` and
`output/webwoven-build-week-demo-preview.mp4`, plus the narrated review file
`output/webwoven-build-week-demo-narrated-preview.mp4`. Render the full-resolution narrated
delivery with:

```bash
pnpm --filter @webwoven/demo-video render:demo:narrated
```

The delivery file is `output/webwoven-build-week-demo-narrated.mp4`, and its matching corrected
caption sidecar is `apps/demo-video/public/captions/voiceover.srt`. Verify the narrated export from
beginning to end before replacing the published YouTube delivery.

The demo composition also accepts an optional Remotion prop named `voiceoverFile`. Put the approved
audio under `apps/demo-video/public/audio/` and pass its public-relative path, for example:

```bash
pnpm --filter @webwoven/demo-video exec remotion render src/index.ts WebwovenDemo \
  ../../output/webwoven-build-week-demo-narrated.mp4 --codec=h264 --crf=18 \
  --props='{"voiceoverFile":"audio/voiceover.mp3"}'
```

The standard picture-only scripts leave this prop empty; the narrated scripts supply the approved
MP3 automatically.
