# Roadmap

Working queue for CYOA.

`CLAUDE.md` is the context document — what this project *is*, and why it is
shaped the way it is. This file is narrower and more perishable: what is
finished, what is being worked right now, and what comes next. When the two
disagree, `CLAUDE.md` wins on architecture and this file wins on sequence.

**Two rules govern this file:**

1. Nothing moves to **Done** while the suite is red. Green first, then the
   roadmap entry.
2. If work changes the architectural state — a new package, a new boundary, a
   resolved open question, a new ADR — `CLAUDE.md` gets updated in the same
   commit. This file never drifts ahead of it.

**Autonomy line.** Items marked **[decide]** resolve an open question in
`CLAUDE.md` and belong to the maintainer, not to an assistant working
unattended. Research and options for them can be produced autonomously; the
decision itself gets asked. Everything else is executable without checking in.

---

## Done

- **Scaffolding and tooling** — repo from template, `foundation.md`,
  `CLAUDE.md`, `pyproject.toml`, `Dockerfile`, `compose.yaml` with Traefik
  labels, `.env.example`.
- **CI and publishing** — lint, format, and test on every push; GHCR image
  build gated on CI passing (ADR-007).
- **Story format specified** — `docs/specs/spec-story-format.md`.
- **The engine** (`engine/`) — `models.py`, `markdown_parser.py`, `graph.py`,
  `state.py`. Pure Python, no framework or database imports. Verified end to
  end against `stories/example/story.md`, which no test uses.
- **The adapters** (`library/`, `storage/`, `web/`) — discovery and catalogue,
  SQLite behind `PlaySessionRepository`, five routes rendered through Jinja and
  htmx. Verified through a real uvicorn boot: the library lists the example
  story, a reader walks it to an ending, progress survives across requests, and
  restart returns to the start passage.
- **v1 reads end to end.** 42 tests, green, no `xfail` left in the suite.
- **Unit tests for `library/` and `storage/`** — 57 new tests, suite 42 → 99.
  Closes the last "Not started" item from v1. See the log entry below.
- **Documentation audit** — every doc in the repo checked against the built
  state; template leftovers removed, stale claims corrected, `compose.local.yaml`
  added so the app can actually be run on a development machine.

## In Progress

Nothing. The queue below is staged and ready to pick up.

## Up Next

Ordered. Take from the top.

1. **Decide what v1.1 is** — **[decide]**
   v1 is now feature-complete and covered. Everything below this line is either
   a deferred quality gate or a roadmap feature, and the roadmap features are
   explicitly listed in `CLAUDE.md` as being "in no committed order". That
   ordering is a maintainer call, not an assistant's. The options, cheapest
   first:

   | Option | Cost | What it buys |
   |---|---|---|
   | Turn on mypy | Config + a pass over annotations | Locks in the type discipline already being written |
   | Coverage gate | Config + a threshold argument | Stops coverage sliding as features land |
   | Twee research | Reading, no code | Resolves an open question that gets more expensive to answer later |
   | Story editor + auth | Large — CRUD, forms, sessions, auth | ADR-006 says editor and auth land together |
   | Multiplayer | Large — **[decide]** on shape first | The thing `state.py` was designed toward |
   | LLM generation | Medium — a provider behind the loader | Breaks constraint 2 unless kept optional and off |
   | Stats / inventory / combat | Medium — **see constraint 1 first** | Most likely to turn this into an RPG engine |

2. **mypy** — **[decide]** on timing, mechanical once decided.
   `CLAUDE.md` calls this deferred, not rejected, and says type hints are being
   written as we go specifically so adoption stays a config change. Worth
   confirming that claim is still true before committing to it: run mypy in
   report-only mode, count the errors, and report the number. If it is near
   zero, turning it on is a `pyproject.toml` block and a CI line.

   *Blocked on a decision, not on work:* mypy is not installed, and adding it
   to the `dev` extra is itself the first half of the decision. Not done
   unilaterally.

3. **Coverage gate** — **[decide]** on the threshold.
   Deferred "until there is enough code for a threshold to mean something".
   With `library/` and `storage/` now unit-tested, there is. The useful next
   step is to measure actual coverage and propose a floor slightly under it, so
   the gate ratchets rather than blocks.

   *Same shape as mypy:* `pytest-cov` is not installed either, so measuring
   means adding a dev dependency first. Left for the maintainer.

4. **Twee format research** — **[decide]** on the outcome; research is free.
   The parser boundary is what keeps this cheap, and `test_library.py` now
   carries tests that exercise a second parser end to end
   (`test_a_second_parser_claims_its_own_extension`,
   `test_both_formats_can_sit_in_one_library`) — so the claim that a new format
   is a new parser class is now checked rather than asserted. Research means:
   what Twee actually specifies, what Twine exports, and whether a
   `TweeStoryParser` really is the whole cost.

5. **Non-test polish, unblocked and small** — no decision needed:
   - `Settings.log_level` is defined and never read; nothing configures logging.
     `compose.local.yaml` sets it to `DEBUG`, which currently does nothing.
   - No route surfaces `validate_story` warnings anywhere an author can see
     them. The library marks a story unplayable on errors, but an author gets
     no way to find out *why* without reading the source.
   - `compose.local.yaml` has never been run — it was written in an environment
     with no Docker daemon. First person to use it should expect to debug it.

## Blocked

Nothing.

---

## Log

Newest first. One entry per completed item — what changed, what it cost, and
anything the next session needs to know.

### 2026-09-18 — Documentation audit against the built state

Every Markdown file in the repo read and checked against the code. Three
classes of problem, all from the same cause — the repo was scaffolded from a
stack-agnostic template and the docs were never re-pointed at the application
that grew in it.

**Template leftovers describing a different repository:**

- `CONTRIBUTING.md` opened "Thanks for your interest in contributing to this
  template" and stated "No CI gate on the template itself — it ships no app
  code, so there's nothing to lint or test at this level." There is a CI gate
  and 99 tests. Its out-of-scope section also declared application code out of
  scope. Rewritten for this project, including the real quality gate and the
  constraints a new feature has to clear.
- `SECURITY.md` said "This is a project template, not a deployed application",
  referenced a `requirements.txt` that does not exist, and claimed Dependabot
  watched npm (it watches pip, docker, and github-actions). Rewritten, with a
  threat model — a story file is untrusted input, and v1's lack of auth is
  deliberate rather than an oversight.
- `scripts/README.md` sent application code to `backend/`, a directory this
  project has never had.
- `CONTRIBUTING.md` referenced `.github/prompts/create-commit.prompt.md`,
  which does not exist. Reference removed.

**Stale claims about the build state:**

- `README.md` said "Most of the engine is not implemented yet — its tests are
  written as `xfail` specifications." The engine has been complete for two
  sessions. Anyone following the README was told the project does not work.
- `tests/README.md` documented the `xfail` convention as current and was
  missing `test_state.py`, `test_library.py`, and `test_storage.py` from its
  layout. The convention is now marked retired rather than deleted — it is
  worth reaching for again, and ADR-008 gained a matching status note.
- `src/cyoa/README.md` said passage ids are `snake_case`; everywhere else says
  lowercase with hyphens or underscores, which is what the loader enforces.

**Docs pointing at the wrong place:**

- `README.md` sent readers to `docs/ADRs/` for architecture decisions. That
  folder is empty — ADR-001 to ADR-010 live in `CLAUDE.md`. Both now say so,
  and `docs/ADRs/README.md` explains when a decision graduates into a file.
- `docs/api/README.md` told the reader to note the framework's generated-docs
  URL and never did. FastAPI serves `/docs`, `/redoc`, and `/openapi.json`
  (verified). Added, along with the route table and the fact that this is a
  server-rendered site rather than a JSON API.
- `docs/plans/README.md` claimed feature roadmaps, which `roadmap.md` now
  holds. Now points there and keeps upstream exploration.

**`compose.local.yaml` added.** `compose.yaml` publishes no ports and joins an
external `proxy` network Traefik is expected to own, so `docker compose up`
fails on a development machine — and the README presented it as the way to
"run it properly". The overlay builds from the working tree, publishes 8000,
and makes the network non-external. **Deliberately not named
`compose.override.yaml`**, which Compose auto-loads: a host deploying from a
checkout would silently pick it up and drop the app off the proxy.

**Not changed, deliberately:** `docs/specs/spec-story-format.md` was verified
against the parser and is accurate — it is the strongest doc in the repo.
`docs/foundation.md` is the founding brief and its intent has not changed, so
it got a status header saying it is kept as written rather than a rewrite. The
four package READMEs under `src/cyoa/` are written as timeless "what belongs
here" guides and had not gone stale.

**Caveat:** `compose.local.yaml` is unverified. This environment has the Docker
client but no daemon, so it was never run. Logged under Up Next item 5.

### 2026-09-18 — Unit tests for `library/` and `storage/`

Closes the one item under "Not started" in `CLAUDE.md`: both packages were
covered only indirectly, through `test_web.py`.

**Added** `tests/test_library.py` (34 tests) and `tests/test_storage.py` (23
tests). Suite: 42 → 99, green. Lint and format clean. **No production code
changed** — no disagreement was found between a docstring's stated contract and
its implementation, and no test was weakened to fit behaviour.

**On the method.** The implementations already existed, so this was
characterization rather than red-green TDD, and every test passed on its first
run. That is exactly the condition under which a test proves nothing, so each
one was then checked against a deliberately broken copy of the code it covers:
12 mutations (permissive slug regex, catalogue dropping broken stories,
validation errors ignored, case-sensitive sort, catalogue cached at
construction, only the first parser consulted, UTC never re-attached, `save`
inserting instead of merging, `session_scope` committing on error, never
committing, `delete` a no-op, history not persisted). All 12 were caught. The
harness was scratch tooling and is not in the repo.

**Fixtures are built in `tmp_path`, not added to `tests/fixtures/stories/`.**
A broken or invalid story added to the shared directory would appear in the
library index `test_web.py` asserts against — the library lists unparseable
stories rather than hiding them, which is the behaviour under test. This is now
recorded as a convention under Code style in `CLAUDE.md`.

**What the tests pin down**, beyond line coverage:

- Path-traversal slugs (`../secrets`, absolute paths, `a/b`, uppercase) are
  refused before touching the filesystem. The traversal cases plant a real,
  parseable story outside the root, so the test fails if the check is removed
  rather than passing because the file happened not to exist. This was
  previously asserted nowhere, and it is what stands between a URL segment and
  the filesystem.
- A second parser claiming `.twee` is dispatched to, receives the raw file text
  unprocessed, and coexists with Markdown in one library.
- The catalogue is re-read per call, so a story dropped into the directory
  appears with no restart — the v1 success metric.
- Naive datetimes out of SQLite are re-attached to UTC. The assertion is a
  comparison against `datetime.now(UTC)`, not just a `tzinfo` check, because
  the real failure is a `TypeError` on a resumed session.
- `session_scope` rolls back on an exception, re-raises the original error, and
  leaves earlier committed work intact.

**Also verified:** the app still boots and plays `stories/example/story.md`
end to end (library lists it, a reader walks to the tagged ending `deeper`,
restart returns to the start, zero validation issues). Walking past an ending
returns 400, which is `advance` refusing a choice from a terminal passage —
correct, not a defect.
