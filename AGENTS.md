# Webwoven Engineering Guidance

## Code organization

- Split code by responsibility and domain.
- Follow the Single Responsibility Principle: each module, class, component, and function has one clear purpose.
- Do not mix business logic, persistence, UI rendering, HTTP handling, or general utilities in one module.
- Prefer small, reusable, composable modules with explicit public interfaces.
- Organize features by domain and keep coupling low.

## Responsibility ownership

- Every rule and piece of state has one owning domain. Scoring owns score calculations, navigation owns path rules, graph access owns graph queries, rooms own race coordination, and UI components own presentation only.
- Other domains consume the owner's public interface instead of duplicating, reaching through, or partially reimplementing its behavior.
- Dependencies point inward toward stable domain contracts. HTTP routes, databases, caches, external APIs, and UI frameworks remain adapters around those contracts.
- Do not create god services, grab-bag utility modules, global mutable stores, or components that fetch data, enforce game rules, and render UI together.
- Shared code must represent a genuine stable concept used by more than one owner. Do not move unrelated helpers into a common module merely to reduce file count.
- Make ownership visible in folder names, module names, tests, and documentation so a new contributor knows exactly where a change belongs.

## File and function size

- Keep authored code files below 600 lines of code.
- The 600-line limit is a final guardrail, not a design target; extract responsibilities earlier when a module becomes difficult to describe in one sentence.
- Generated code, lockfiles, database migrations, and schemas are exempt and must not be hand-edited.
- Extract services, components, repositories, validators, or domain modules before a file approaches the limit.
- Keep functions focused and favor readable control flow over clever compression.

## Documentation

- Update the relevant page under `docs/` whenever behavior, a public contract, data rules, or operations change.
- Update the current Build Week log for every milestone.
- Record decisions in an ADR when they affect more than one subsystem.
- Never publish secrets, private transcripts, hidden reasoning, or raw local-environment output.

## Validation

- Run the narrowest relevant checks while iterating, then the complete quality gate before publishing.
- Runtime gameplay must never call Wikidata, Wikimedia Commons, or an AI service.
- Codex-assisted content is a reviewed build artifact, never a runtime dependency. Label its
  provenance truthfully as `generator: codex` when model metadata is unavailable.
- Preserve source, license, prompt, graph-build, and generator provenance wherever applicable.
- Purple, gradients, glassmorphism, neon, and arbitrary colors are not part of the design system.
