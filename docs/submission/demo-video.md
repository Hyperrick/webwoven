# Demo video production plan

The exact narration is in [`demo-voiceover.txt`](demo-voiceover.txt). It uses short sentences and
plain words for TTS. The replacement source MP3 runs for 190.928938 seconds. Remotion plays it at
1.09×, for an effective narration duration of approximately 175.164 seconds. The 178-second
composition remains safely below the three-minute limit.

## Replacement narration

- The replacement audio is `apps/demo-video/public/audio/voiceover.mp3`.
- It uses a calm, clear English voice with short pauses between paragraphs. The source narration
  contains no music; the final mix adds the credited background track below at a subtle level.
- Its measured source duration is 190.928938 seconds and its composition playback rate is 1.09×.
- The corrected sidecar captions are `apps/demo-video/public/captions/voiceover.srt`.
- The narration starts after a one-second composition delay; its first audible sample is at
  approximately 1.126 seconds in the rendered review file.
- The SRT contains 40 corrected, retimed, non-overlapping cues and ends at 176.138 seconds.
- The final picture holds for approximately 1.84 seconds after the effective narration ends.

The eight scene boundaries are aligned to the measured paragraph starts in the replacement audio.
Silent renders remain available for picture-only review, but the Devpost delivery is the narrated
render. The previous YouTube upload was deleted, so there is no public demo URL until the owner has
uploaded the verified replacement. The upload artwork remains at
`docs/assets/submission/youtube-thumbnail.png`.

The V2 edit replaces the stale Relay, Par, and 40-route presentation. Its product captures use the
current Multiplayer and Lobby language, keep Target visible without a Par field, show the compact
phone HUD, and report all 100 checked start/goal rounds.

## Music credit

The final demo uses a quiet background track beneath the narration:

[Music by Gleb D](https://pixabay.com/users/glebator-51558515/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=565742)
from [Pixabay](https://pixabay.com/music//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=565742).

Include this credit and both links in the public YouTube description.

The repository copy is `apps/demo-video/public/audio/background-music.mp3`. The reusable Remotion
track starts at 0, fades to a default volume of 0.055 over two seconds, and fades out over the final
three seconds so the narration remains dominant.

## Remotion-ready storyboard

| Scene             |    Final time | Narration   | Visual                                                                                                              |
| ----------------- | ------------: | ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Hook              | 0:00.0–0:12.0 | Paragraph 1 | Start on the current real node map, then show the Webwoven name and goal.                                           |
| Start a round     | 0:12.0–0:28.7 | Paragraph 2 | Show the current Single-player setup with difficulty and topic, then the round introduction.                        |
| Explainable moves | 0:28.7–0:55.4 | Paragraph 3 | Return to the node map, open the Rosario connection, and show the fact, picture, source, and hints.                 |
| Three modes       | 0:55.4–1:15.9 | Paragraph 4 | Show Single player, the Daily result board, and Multiplayer with the current Lobby language.                        |
| Codex and GPT-5.6 | 1:15.9–1:46.8 | Paragraph 5 | Name Codex and GPT-5.6 Sol, then show the architecture, focused source folders, tests, and human-directed workflow. |
| Iteration         | 1:46.8–2:13.5 | Paragraph 6 | Pair current desktop and phone views with the final playtest improvements.                                          |
| Trust boundary    | 2:13.5–2:43.8 | Paragraph 7 | Show the checked local-atlas size, 100 checked rounds, deterministic rules, and zero runtime AI calls.              |
| Close             | 2:43.8–2:58.0 | Paragraph 8 | End on the route result with the live URL and the line “Connect anything, and discover why it is connected.”        |

## Visual rules

- Use actual Webwoven footage and repository evidence, not generated UI mock-ups.
- Keep most cuts between three and eight seconds so the judge can read the screen.
- Use simple crossfades and gentle zooms; avoid flashy transitions.
- Put short captions only where they add proof: `3 play modes`, `GPT-5.6 Sol + Codex`,
  `3,970 entities`, `22,402 connections`, and `No runtime AI calls`.
- Never show secrets, private transcript text, hidden reasoning, local environment values, or
  unrelated browser tabs.
- Do not add decorative third-party logos or unlicensed promotional media or music. Include every
  credit required by the license of an approved third-party asset.
  Real gameplay footage may retain the source-backed entity names and documentary media recorded
  in the attribution ledger; the entrant must complete the final rights review before submission.

## Implemented Remotion workflow

The production project lives in `apps/demo-video`. It defines two 1920×1080, 30 fps
compositions:

- `WebwovenDemo`: the 2:58 replacement Build Week edit, matching the eight storyboard scenes above.
  It contains 5,340 frames at 30 fps.
- `WebwovenTeaser`: a 24-second review cut that opens on the node map, shows real gameplay, and
  closes on the product line.

Product visuals use the current interface captured from the rebuilt Compose acceptance surface at
`http://localhost` and deterministic demo surfaces for reproducible Daily and Multiplayer states.
The gameplay capture is a real 1920×1080 Solo route from Lionel Messi through Rosario, Argentina,
UNESCO, and France to Tour de France. It is stored for Remotion as
`apps/demo-video/public/captures/current-gameplay.mp4`; the refreshed setup, Daily result,
Multiplayer Lobby, mobile, and node-map stills are under `apps/demo-video/public/images/`.

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
pnpm --filter @webwoven/demo-video render:demo:narrated:rough
```

These write `output/webwoven-teaser-preview.mp4` and
`output/webwoven-build-week-demo-preview.mp4`, the narrated 960×540 review file
`output/webwoven-build-week-demo-v2-preview.mp4`, and the deliberately compressed 480×270 approval
file `output/webwoven-build-week-demo-v2-rough-preview.mp4`. Render the full-resolution narrated
delivery with:

```bash
pnpm --filter @webwoven/demo-video render:demo:narrated
```

The approved delivery is `output/webwoven-build-week-demo-v2.mp4`, and its matching corrected
caption sidecar is `apps/demo-video/public/captions/voiceover.srt`. The final export is 2:58,
1920×1080 at 30 fps, with H.264 video and 48 kHz AAC stereo audio. It measures −15.4 LUFS with a
−0.7 dBFS true peak. Its SHA-256 is
`cc8db746a36fcc3d11554d74dd41c13c4e759c69214f9d28cdad5770350437b0`.

The first frame is black and reveals the Hook over 18 frames. The Hook's dark browser chrome reaches
the top edge without the former light strip. The narration waits one second before starting. The
final 18 frames fade the closing card back to black. The Explain scene uses a reserved two-row layout
so its full one-line heading cannot intersect the product browser. Encoded-frame checks passed at
the opening, Start headline, 2:14 Trust transition, 2:44 Close transition, and final fade. Upload the
full-resolution video with the copy and settings in
[`youtube-upload.md`](youtube-upload.md), then add the public URL to the repository and Devpost
draft.

The demo composition accepts optional Remotion props named `voiceoverFile`,
`narrationPlaybackRate`, `musicFile`, and `musicVolume`. Put the replacement audio under
`apps/demo-video/public/audio/` and pass its public-relative path, for example:

```bash
pnpm --filter @webwoven/demo-video exec remotion render src/index.ts WebwovenDemo \
  ../../output/webwoven-build-week-demo-v2.mp4 --codec=h264 --crf=18 \
  --props='{"voiceoverFile":"audio/voiceover.mp3","narrationPlaybackRate":1.09,"musicFile":"audio/background-music.mp3","musicVolume":0.055}'
```

The standard picture-only scripts leave both audio files empty. The narrated scripts supply the
replacement voiceover and credited music, using the composition's 1.09× narration playback rate
and subtle 0.055 music level automatically.
