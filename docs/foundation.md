# CYOA — Foundation
**Status**: Draft v0.1
**Date**: 2026-09-18

---

## The Problem

There isn't one, and the project is better for saying so plainly.

CYOA exists because building a story engine is enjoyable. The maintainer's words: *"the fun is in building the engine, story is an excuse."* That is the whole motivation, and it is a legitimate one — but it is a different motivation from solving a problem, and it implies different priorities.

What follows from it:

- **The engine is the product.** Not the stories, not the reading experience, not a content library. Work that makes the engine more interesting to build is worth doing; work that turns this into a content-management chore is not.
- **Content comes from elsewhere.** Stories will be written by people close to the maintainer, or generated with an LLM. The engine therefore has to run stories it has never seen, written by people who never read its source. Generality is not gold-plating here — it is the actual requirement.
- **Scope pressure runs toward the engine, not away from it.** The features most likely to eat the project — an editor, accounts, an RPG stat system — are the ones that add the least engine. v1 defers all of them deliberately.

The thing that would make this project a failure is not shipping late. It is ending up maintaining a CMS.

## The Solution

A containerized application someone self-hosts. Once running, it serves a digital choose-your-own-adventure book — a text adventure read in a browser.

Concretely, for v1:

- A story is a Markdown file with YAML frontmatter, one folder per story, dropped into a `stories/` directory
- The app discovers whatever it finds there and lists it in a library
- A reader picks a story, reads a passage, picks a choice, and moves through the branching graph until they reach an ending
- Progress is saved in SQLite so a reader can come back
- It runs as a single container behind Traefik, with no companion services required

Underneath, the engine is a pure Python library: a story model, a parser, a graph validator, and state transitions. The web layer is a thin adapter over it. That separation is not architectural decoration — it is what makes the roadmap (a CLI client, multiplayer, a different story format, LLM generation) additive rather than a sequence of rewrites, which is what keeps the project fun to keep building.

Validation deserves specific mention, because it is where a story engine earns its keep. The mistakes authors actually make are graph mistakes: a choice pointing at a passage that was renamed, a section orphaned by a typo, a branch that stops mid-sentence. Catching those before a reader hits them is most of the value the engine provides to an author who is not a programmer.

## The User

Two people, with different needs, and neither of them is a customer.

**The maintainer**, who self-hosts it and is building it for enjoyment. Runs it on a homelab alongside everything else, behind Traefik, at `cyoa.castaldifamily.com`.

**Authors** — people close to the maintainer, plus LLMs used as generators. They write stories; they do not read the source, run the test suite, or know what a passage id is until told. Everything they touch is a Markdown file and a folder name. This is the constituency that makes story-format legibility and graph validation matter.

**Readers** exist but are barely specified: whoever is handed the URL. The reading experience should be clean and work on a phone, and beyond that v1 has no ambitions for them.

A general self-hosting public is explicitly *not* the user, though the project should not gratuitously exclude them — hence the example story shipping in the image, and the public host being configurable rather than hardcoded.

## What We Are Not Building

Almost nothing here is a permanent *never*. It is a v1 boundary and a roadmap, which is an honest description of a hobby project.

**Not in v1:**

- **A story editor.** Stories are hand-edited or LLM-generated files. An editor means CRUD forms and an auth story — the least interesting work available.
- **Authentication.** No accounts, no login, no admin. Arrives with the editor.
- **Multiplayer.** But the foundation is laid: play state belongs to a session with a list of participants, not to a single implied reader.
- **Live LLM generation at read time.** Pre-authored files have to work first. When it comes, the app calls the API itself with a key from the environment.
- **Stats, inventory, combat.** Interesting, undecided, and the thing most likely to turn a narrative engine into an RPG engine.
- **Anything non-text.** Images and audio come later, if at all — "just text for the first few generations."

**Genuine constraints, not deferrals:**

- Story content is **never** `eval`'d. When conditions arrive, they get a restricted evaluator, because a story file is something a stranger can hand you.
- v1 makes **no** outbound network calls. It plays offline.
- It runs as a **single container**. No required database server, no sidecar.

## Success Metric

> Someone drops a story they wrote — or had an LLM write — into `stories/`, it appears in the library at `cyoa.castaldifamily.com`, and plays start to finish with no code changes.

The pressure in that sentence is on *someone else's story*. It is easy to build an engine that runs the story you tested it with. The metric is met when the engine is general enough to run one it has never seen.

## Open Questions

- **Twee.** Markdown + frontmatter is the v1 format, but Twee is an established interactive-fiction standard, and the Twine visual editor authors it for free — which could replace building an editor at all. To be researched. The parser boundary exists so that switching, or supporting both, stays cheap.
- **What multiplayer actually means.** Readers moving through one book together and agreeing on choices, or readers moving independently in a shared world? The current state model assumes the former. Worth deciding before building, not during.
- **Whether stats and inventory ever happen.** Undecided.
- **How the v2 editor authenticates.** A built-in admin password is portable for any self-hoster; Traefik plus Authentik forward auth matches the existing homelab and needs less code. Not decided.

---
*This document is the source of truth for product intent. Architecture and technology decisions live in `docs/ADRs/` and the decision log in `CLAUDE.md`; this file is about why, not how.*
