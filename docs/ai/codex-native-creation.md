# Codex-native creation workflow

Codex is Webwoven's development collaborator. The existing Codex subscription, skills, and
parallel agents support the application, documentation, tests, prompts, content, illustrations,
and public build journal. This is the practical evidence behind the project's message:

> Everyone with an idea can become a game developer.

The primary application-building task ran on GPT-5.6 Sol in Codex. The project owner supplied the
concept, steered implementation, selected the final product and design decisions, reviewed the
result on real desktop and mobile surfaces, and retained approval over external services,
infrastructure, releases, and submitted claims. Codex translated those decisions into modular
domain work, coordinated parallel implementation and review tasks, and repeatedly exercised the
result through the repository's automated and manual acceptance surfaces.

## Artifact workflow

1. Supply an approved set of Wikidata fact IDs and a versioned prompt.
2. Use Codex during development to draft hint wording, relationship explanations, or a
   Cartographer recap from only those facts.
3. Validate the result against its strict JSON Schema and deterministic grounding rules.
4. Reject malformed output, unsupported facts, target-answer leaks, non-English content, and
   anything not explicitly approved.
5. Have a human editor review and approve the surviving artifact.
6. Compile approved content into an immutable static pack committed to the repository or attached
   to a checksum-verified GitHub Release.

Every record preserves the prompt, generation date, fact hash, output hash, validation results,
approval status, and a truthful `generator: codex` provenance label. The project does not claim a
particular API model when that metadata is unavailable.

The executable envelope is committed as
`data/manifests/codex-content-artifact.schema.json`. Validate an approved draft against its exact
fact pack with:

```sh
uv run --package webwoven-pipeline webwoven-pipeline validate-codex-artifact \
  --fact-pack path/to/facts.json \
  --artifact path/to/approved-artifact.json
```

The validator executes that committed Draft 2020-12 schema, including its date-time formats and
length limits, before it can record `schema:passed`. Semantic validation then applies three
independent gates:

- Hint target labels and aliases must remain absent.
- English evidence must dominate supported non-English marker sets, and non-Latin prose is
  rejected.
- Every factual token must occur in the cited fact's subject, relationship, or object. Only a
  small claim-neutral navigation vocabulary is allowed around those exact surfaces. Recaps may
  additionally use the supplied start and target labels and the derived route length.

This conservative rule intentionally rejects unsupported paraphrases. Prompts should preserve the
supplied fact wording, and human editorial review remains mandatory after automated validation.

## Runtime boundary

Production performs no AI calls and accepts no AI credentials. Generated wording never
selects facts, legal moves, hints, scores, or winners. Every content type also has deterministic
fallback copy, so the game remains complete when an assisted artifact is absent or rejected.
