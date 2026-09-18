# Contributing

This is a solo-maintained hobby project. The bar is "does it keep the engine pleasant to work on", not ceremony — but the quality gate below is real, because CI enforces it.

## Workflow

No issue required. If you spot something wrong or missing, go straight to a branch.

### 1. Branch

Use the branch-workflow prompt (`.github/prompts/branch-workflow.prompt.md`) or follow the naming convention directly:

```
feature/short-description
fix/short-description
docs/short-description
refactor/short-description
test/short-description
experiment/short-description
```

Keep them short, descriptive, and lowercase with hyphens. Branches opened by an assistant are prefixed `claude/` instead.

### 2. Make your changes

Work atomically — one logical change per commit. Conventional Commits format is **expected**, not optional:

```
feat(engine): add the Twee parser
fix(web): stop a renamed passage stranding a reader
docs(readme): correct the local run instructions
test(storage): cover the repository round trip
```

The scope is usually the package you touched — `engine`, `library`, `storage`, `web` — or `ci`, `docs`, `deps`.

### 3. Pass the quality gate

CI runs three commands. Run them before you push and there are no surprises:

```bash
ruff check .            # lint
ruff format --check .   # format
pytest                  # tests
```

All three must be green. A few specifics worth knowing:

- **Line length is 100**, and `ruff format` will sometimes want a signature on one line that lint then rejects at 101 characters. Shorten the name rather than fighting the formatter.
- **Public functions, classes, and modules carry docstrings**, and they should say *why*. The interesting comments in this codebase explain a decision, not a mechanism.
- **Public functions and methods carry type hints.** mypy is not enabled yet; annotating as we go is what keeps turning it on a config change rather than a refactor.
- **Tests that need a story on disk build it in `tmp_path`**, not in `tests/fixtures/stories/`. See `tests/README.md` for why.

### 4. Open a PR

Fill in the PR template. CI must be green before merge.

### 5. Merge

Squash or merge commit, your call.

---

## Before you add a feature

Read the Constraints section of `CLAUDE.md` first. Five of them are non-negotiable, and the first one — **never `eval` story content** — is the one a plausible-looking shortcut will walk you straight into the moment passages get conditions.

The architectural rule that governs everything else: **the engine is a pure library, and `web`, `storage`, and `library` are adapters over it.** Dependencies point inward. If a change forces edits across three packages, the boundary has eroded; stop and fix that rather than pushing through.

`roadmap.md` tracks what is queued. Items marked `[decide]` resolve an open question in `CLAUDE.md` and are the maintainer's call — bring a proposal rather than an implementation.

## What's in scope

- Anything in the engine, the adapters, or the story format
- Story content in `stories/`
- Tests, CI, tooling, and documentation
- Bug fixes anywhere

## What's out of scope

- **Anything that breaks a constraint in `CLAUDE.md`** — `eval`, a required companion container, outbound network calls in the default configuration, secrets in the repo, or story-file syntax leaking outside the parser layer
- **A frontend build step.** ADR-002 is deliberate: server-rendered HTML and vendored htmx, no bundler, no `node_modules`
- **Resolving an open question by implementing it.** Multiplayer shape, stats and inventory, the editor's auth model, and the Twee decision get decided before they get built
