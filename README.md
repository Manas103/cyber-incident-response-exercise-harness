# Cyber Incident Response Exercise Harness

A tabletop-exercise harness for a simulated regional utility: 6 incident-response scenarios, each
with a written 4-step playbook, 30 timestamped injects (5 per scenario), and a deviation detector
that diffs a responder's actual action log against the playbook and names every deviation by step,
inject and kind. Time-to-detect and time-to-contain are measured per inject against the playbook's
own definition of a detect/contain action, and an after-action report refuses to mark any of the 24
named playbook steps "exercised" without a linked evidence artifact. Python 3.12, FastAPI,
SQLAlchemy, PostgreSQL (SQLite fallback), React 18 + TypeScript + Vite + Vitest. Every number below
was measured on this machine by running the commands shown, not written backward into the code to
match a target. Extended (Aug. 2026) with `incident_harness/intake/`: 3 incoming report channels
(customer report, internal alert, researcher disclosure) normalized onto one incident record,
severity classified against a written matrix checked by an independent reference oracle, and every
customer notification held behind a named human approval. Extended again (Sep. 2026) with
`incident_harness/vendor/`: 4 vendor-shaped alert feeds (endpoint detection, email gateway, identity
provider, managed-detection escalation) correlated by shared entity and time onto one incident
record, severity and time-to-detect/time-to-contain scored the same way, and executable containment
(host isolation, session revoke, token reset) that runs only behind a named approver and that always
records enough state to be undone exactly.

## Why this exists

A tabletop exercise that produces only a facilitator's narrative memory of "it went fine" is not
auditable and does not improve the next exercise. This is a small version of the artifact an
incident-response function actually needs after running a tabletop or live-fire exercise: a written
playbook per scenario that exists before the exercise runs (not reverse-engineered from what
happened), a mechanical diff between what the playbook expected and what the responder log actually
shows, and an after-action report that will not credit a step as rehearsed unless there is a
specific artifact proving it was.

## Honest framing, up front

- **This is a tabletop-exercise harness, not a live intrusion-detection or SOAR system.**
  `incident_harness/detector.py` compares a *recorded* responder action log against a *written*
  playbook; it does not itself detect intrusions, ingest real EDR/SIEM telemetry, or take any
  containment action. The "detect" and "contain" actions in every fixture are the responder's own
  logged actions, not an automated classifier's output.
- **The 6 scenarios and their playbooks are a designed, defensible exercise plan, not a scraped or
  copied one.** `incident_harness/scenarios.py` fixes a deliberately narrow 4-phase taxonomy
  (detect, contain, eradicate, recover), a simplification of NIST SP 800-61's six-phase lifecycle:
  Preparation and Post-Incident Activity are exercise-design and after-action concerns, not things a
  responder does in reaction to a single inject, so they are not modeled as inject-triggered
  playbook steps. 6 scenarios x 4 phases = the 24 named playbook steps the after-action report
  covers.
- **Every inject, action log, and evidence record in this repo's tests and benchmarks is synthetic.**
  `incident_harness/fixtures.py` and `incident_harness/injects.py` describe a fictional utility's IT
  and OT/SCADA estate with no real company, incident, vendor, or employee behind any of it.
- **The deviation detector is a deterministic sequence diff, not a machine-learning anomaly
  detector.** `detect_deviations` in `detector.py` checks step presence, step identity, and relative
  timestamp order against a fixed 4-step playbook; there is no scoring, no threshold, and no
  training data anywhere in the scored path.
- **The database is real PostgreSQL when configured, a real on-disk SQLite file otherwise.**
  `incident_harness/db.py` reads `INCIDENT_DATABASE_URL`; PostgreSQL is not running as a service on
  this machine, so every measurement below ran against the SQLite fallback, exercising the same
  SQLAlchemy models a Postgres deployment would use. `tests/test_postgres_fallback.py` probes for a
  real reachable Postgres and skips cleanly (not a failure) when there is none, exactly as
  `ai-governance-audit-readiness-register` does.
- **The console is a real, typed client wired to the real FastAPI endpoints, tested against a mocked
  `fetch`, not a live backend integration run in the same automated pass.** `src/api.ts` and
  `src/types.ts` are typed directly against `incident_harness/schemas.py`'s actual response shapes;
  `vite.config.ts` proxies `/api` to `localhost:8000` for real manual use.
- **Machine and toolchain.** 8 physical / 16 logical cores, Windows 11 Home 10.0.26200. Backend:
  Python 3.12.10, FastAPI 0.141.1, Starlette 1.6.0, SQLAlchemy 2.0.52, Pydantic 2.13.4, pytest
  9.1.1, httpx 0.28.1 (TestClient), psycopg2-binary 2.9.12 (real deployment target, not exercised
  live). Console: Node.js v22.17.1, npm 10.9.2, Vite 5.4.21, React 18.3.1, TypeScript 5.6.3, Vitest
  2.1.9 with jsdom and Testing Library.

**Intake extension (`incident_harness/intake/`), honest framing:**
- **The 3 channels are deliberately not unified into one input shape at the source.**
  `CustomerReportRaw`, `InternalAlertRaw` and `ResearcherDisclosureRaw` each carry the fields
  that channel genuinely has (an account id and an email; an alert id and a source system; a
  researcher handle and a disclosure channel); `normalize_*()` is where the real reconciliation
  work happens, onto one shared `IncidentRecord`. Making the three raw shapes identical up front
  would remove the thing the resume bullet actually claims.
- **The severity matrix is a fixed, ordered rule table over 3 inputs (data sensitivity, scope,
  active exploitation), not a learned or scored model.** `intake/severity.py` writes the rules
  out in the order a reviewer would read them, most severe first; `classify_severity` is a plain
  top-to-bottom walk, no weighting, no threshold. The independent reference oracle
  (`reference_severity_oracle.py`) is a differently-shaped nested if/elif tree built from the
  same written rules, not a renamed copy, exactly the contrast `detector.py`/`reference_detector.py`
  already draws above for the deviation detector.
- **Every incident, approver name and channel payload in this module's tests and benchmarks is
  synthetic**, describing the same fictional regional utility the rest of this repo already uses,
  not a real customer, employee or researcher.
- **The notification gate checks that an approver is *named*, not that the approval is
  authorized or that the named person actually exists in any directory.** `send_notification`
  refuses an empty or blank `approved_by`; it does not verify the approver against a real
  identity or role store, which a production version would need and this build does not model
  (see Limitations).
- **Machine and toolchain (this extension).** Windows 11 Home 10.0.26200, Python 3.12.10,
  pytest 9.1.1.

**Vendor extension (`incident_harness/vendor/`), honest framing:**
- **The 4 feeds carry genuinely different entity shapes, not a cosmetic relabeling of the 3
  intake channels.** `feeds.py`'s raw dataclasses mirror what each vendor type can actually
  see: an EDR console sees a host, never a user principal; an email gateway sees a recipient
  user, never a hostname; an identity provider sees a user and a source IP; only a managed-
  detection-and-response vendor's own escalation, which already triaged across tools before
  naming it to the client, carries both. `correlate_vendor_alerts` has to reconcile that
  mismatch to fold 4 differently-shaped feeds into one incident, which is a different problem
  from intake's 3-channel normalization (same 3 facts, 3 different envelopes).
- **"Entity-and-time correlation" is a literal graph, not a shared label a fixture generator
  attached.** Two alerts are linked when they share at least one `(entity_type, value)` pair
  and land within a 2-hour window of each other; one incident is one connected component.
  `correlation.py` builds the graph and traverses it by BFS; `reference_correlation.py` is an
  independently coded disjoint-set (union-find) oracle over the same pairwise test, with its
  own, differently-shaped aggregation step, sharing no helper function with the primary.
- **Containment is state change, not a message hold.** `containment.py` generalizes
  `intake/notification.py`'s named-approval gate from "hold a message" to "flip a target
  entity's state", over an in-memory `EntityStateStore` standing in for a live EDR/IdP/SOAR
  platform the same way `device-telemetry-policy-middleware`'s policy plane stands in for a
  live vendor API. Every executed action's prior state is recorded, so `undo_containment` can
  restore it exactly; this build verifies that empirically (every executed action in the
  100-case gate benchmark is actually reverted, not assumed reversible from the code's shape).
- **Severity reuses the same written matrix, not a second one.** The claim is the same 3-input
  matrix (`intake/severity.py`) scored against a different population (vendor-incident-derived
  inputs instead of report-channel-derived ones); writing a second matrix for the same written
  rules would be duplication the design-first-then-reuse policy explicitly argues against.
- **Machine and toolchain (this extension).** Windows 11 Home 10.0.26200, Python 3.12.10,
  pytest 9.1.1.

## Architecture

```
backend/
  incident_harness/
    scenarios.py           the fixed 6 scenarios and their 24 named playbook steps
                            (4 phases each: detect, contain, eradicate, recover)
    injects.py              the fixed 30 injects (5 per scenario), each with a timestamp
    detector.py              the primary deviation detector: dict/set based, O(steps + actions)
    reference_detector.py     an independent, deliberately differently-shaped
                            reimplementation (linear/quadratic scans, no dict or set),
                            diffed exactly against detector.py
    timing.py                 time-to-detect / time-to-contain per inject
    fixtures.py                seeded 40-run deviation fixture, seeded 40-run clean
                            fixture, and the 6 official demo runs, all with known
                            ground truth
    after_action.py              the after-action report and its evidence gate
    models.py                     SQLAlchemy tables: scenario, playbook_step, inject,
                            run, responder_action, evidence_artifact
    db.py                          real PostgreSQL if INCIDENT_DATABASE_URL is set and
                            reachable, else a real on-disk SQLite fallback
    seed.py                         seeds the fixed reference data and a fully
                            evidenced demo exercise into the database
    schemas.py                      Pydantic response shapes, typed 1:1 against
                            what src/types.ts expects on the console side
    api.py                           FastAPI app: scenarios/injects timeline, run
                            detail (actions, timing, deviations), after-action report
  scripts/
    init_db.py                       stands up the schema (and seeds it) against
                            whatever database is configured
    run_deviation_benchmark.py        the 40+40-run benchmark behind the seeded-
                            deviation-recall and false-flag claims
    run_evidence_gate_check.py         demonstrates the after-action refusal path
                            and the success path against the same 6 official runs
  tests/                               46 pytest tests (unit, reference-oracle diff,
                            invariants, after-action, API, Postgres fallback)
  docs/                                 test_output.txt, deviation_benchmark_output.txt,
                            evidence_gate_output.txt, frontend_test_output.txt
frontend/
  src/
    types.ts                          typed 1:1 against incident_harness/schemas.py
    api.ts                             listScenarios, listInjects, listRuns, getRun,
                            getAfterActionReport
    components/
      ScenarioTimeline.tsx              injects grouped by scenario, ordered by
                            timestamp: the scenario/inject timeline view
      DeviationsPanel.tsx                deviations for a selected run, naming the
                            step, run and deviation type: the deviations-flagged view
      AfterActionReport.tsx               exercised/not-exercised status per named
                            playbook step, with the reason and evidence reference
    App.tsx                              wires the timeline, run list, deviations
                            panel and after-action report to the real API
```

### Intake extension (`incident_harness/intake/`)

```
incident_harness/intake/
  channels.py            3 raw channel shapes (CustomerReportRaw, InternalAlertRaw,
                         ResearcherDisclosureRaw) and normalize_*() onto one shared
                         IncidentRecord.
  severity.py             The written matrix: SeverityInputs, MATRIX_RULES (an
                         ordered list of (predicate, severity) pairs), classify_severity().
  reference_severity_oracle.py  An independently-shaped nested if/elif reimplementation,
                               diffed exactly against severity.py.
  notification.py          NotificationRequest/NotificationResult, send_notification():
                         refuses without a named approver.
  models.py                 IncidentRecordRow, NotificationRow (shares the main Base).
  schemas.py                 Pydantic request/response shapes for the 5 new routes.
  api.py                      register_intake_routes(): 3 channel-ingest endpoints,
                         a listing endpoint, and the notification endpoint.
  fixtures.py                  Seeded generators for all 3 benchmarks below.
scripts/
  run_intake_benchmark.py       All 3 benchmarks in one run.
tests/
  test_intake_channels.py        Normalization and the 3-channel equivalence property.
  test_intake_severity.py          The written matrix plus a 500-case oracle diff.
  test_intake_notification.py       The approval gate, unit and seeded.
  test_intake_api.py                 Real FastAPI TestClient, all 5 routes.
```

### Vendor extension (`incident_harness/vendor/`)

```
incident_harness/vendor/
  feeds.py                4 raw feed shapes (EndpointDetectionRaw, EmailGatewayRaw,
                         IdentityProviderRaw, ManagedDetectionEscalationRaw) and
                         normalize_*() onto one shared VendorAlert.
  correlation.py            Primary entity-and-time correlation: adjacency-list graph,
                         BFS connected components, VendorIncident aggregation.
  reference_correlation.py   Independent union-find oracle, diffed exactly against
                         correlation.py; its own aggregation step, no shared helpers.
  containment.py             ACTION_HOST_ISOLATION/SESSION_REVOKE/TOKEN_RESET,
                         EntityStateStore, apply_containment(), undo_containment().
  playbook.py                 The written detect/contain playbook definition.
  timing.py                    compute_vendor_timing() against playbook.py.
  models.py                     VendorAlertRow, AnalystAckRow, ContainmentActionRow
                         (shares the main Base; incidents are recomputed from
                         VendorAlertRow on every read, never stored).
  schemas.py                     Pydantic request/response shapes for the 8 new routes.
  api.py                           register_vendor_routes(): 4 feed-ingest endpoints,
                         a derived incident listing, an ack endpoint, and the
                         containment create/undo endpoints.
  fixtures.py                       Seeded generators for all 3 benchmarks below.
scripts/
  run_vendor_benchmark.py              All 3 benchmarks in one run.
tests/
  test_vendor_feeds.py                   Each feed normalizes to the right entity shape.
  test_vendor_correlation.py               25/25 chains fold to 1 incident, 0/20 false groupings.
  test_vendor_correlation_oracle_diff.py     Primary vs. reference, exact agreement.
  test_vendor_severity.py                      500-case oracle diff over vendor-derived inputs.
  test_vendor_timing.py                          Time-to-detect/contain against playbook.py.
  test_vendor_containment_gate.py                  100-case gate + full reversibility check.
  test_vendor_api.py                                 Real FastAPI TestClient, all 8 routes.
```

### Design deep-dives

**A playbook step is scenario-level, not inject-level, on purpose.** 30 injects share only 24 named
steps because a real playbook does not invent a bespoke response procedure per event; two ransomware
injects in the same scenario both call for the same "isolate affected hosts" containment step. This
is also why `detect_deviations` operates per run (one inject's full response episode), not per
playbook step in isolation: a run's actions are checked against the whole 4-step sequence of its own
scenario at once, which is what makes the out-of-order deviation type meaningful.

**Seeding exactly one deviation per run is harder than it looks, and getting it wrong is the real
bug this build found (see Findings).** `fixtures.py` builds each seeded-deviation run so that
corrupting one thing never accidentally introduces a second, independent deviation: `missing_step`
drops one action and leaves the other three untouched and in order; `wrong_step` keeps all four
correct actions and adds one extra action naming a step from a *different* scenario's playbook, so
the correct step is never simultaneously "missing"; `out_of_order` keeps all four correct step
identities and swaps only the timestamps of one adjacent pair, so nothing is missing or foreign.

**The reference oracle is a genuinely different algorithm, not a renamed copy.** `detector.py`
builds a dict of the earliest action per expected step and a set-membership check for what counts as
"foreign". `reference_detector.py` never calls `dict()` keyed by step id for lookups or uses `in` on
a set; it does a manual linear scan of the raw action list for every step, and a quadratic pairwise
scan (every earlier-order step compared against every later-order step, not just adjacent pairs) for
the ordering check, reaching the same conclusion by a different route. `tests/test_reference_oracle_diff.py`
includes a structural guard that the reference file never imports `detect_deviations` itself.

**The API never persists a deviation or a timing verdict; it recomputes both on every read.**
`get_run` in `api.py` re-derives timing and deviations from the current `responder_action` rows every
time a run is requested, exactly as `ai-governance-audit-readiness-register` never persists a
verdict, for the same reason: a stored deviation list would go stale the moment an action is
corrected.

**Vendor incidents are derived the same way, for the same reason, and that forced a real design
decision about containment state.** `list_vendor_incidents` in `vendor/api.py` reruns
`correlate_vendor_alerts` over every stored `VendorAlertRow` on every GET; nothing about incident
membership is ever written down as a fact of its own. Containment state follows the same
"derive, don't store" rule: rather than a mutable `current_state` column that could drift from the
`ContainmentActionRow` audit log that is supposed to explain it, an entity's current state is always
recomputed as "the most recent executed, not-undone action's resulting state, or normal if there is
none" (`_current_state_of_entity`). The in-process `EntityStateStore` from `containment.py`'s unit
tests is reconstructed fresh for every single API call from that same derived state, not kept alive
across requests, so the pure functions `apply_containment`/`undo_containment` stay identical whether
they are called from a unit test or from a FastAPI route.

**The first real integration bug here was a missing clock, not a logic error.** `apply_containment`
and `undo_containment` are pure and timestamp-free by design (see `containment.py`); but
`time_to_contain_minutes` has to be measured against *something*, and the API's first draft
computed it as `incident.start_minutes` itself whenever any containment action had executed,
`first_contain.id and incident.start_minutes if ... else None`, which is a truthy-`id` short-circuit
that always evaluated to the incident's own start time, making every time-to-contain measurement
exactly 0 regardless of when containment actually happened. The fix was not in the timing math, it
was that `ContainmentRequest`/`ContainmentActionRow` had no field at all for "when, on the
simulated-exercise clock, did this action happen", only a wall-clock `created_at`; `action_minutes`
was added to the request, the row, and the schema, and `compute_vendor_timing` was pointed at it.
`tests/test_vendor_api.py::test_ack_and_executed_containment_produce_timing` asserts the actual
minute value (`30`, not `0`) specifically so this class of bug cannot silently return.

## Validation

1. **Unit tests** (`pytest`), covering the scenario/playbook fixed design (6 scenarios, exactly 24
   named steps, one per phase), the 30-inject timeline, the detector (one hand-built example per
   deviation type plus the clean case), and timing (never negative, uses the earliest matching
   action, ignores foreign-scenario actions).
2. **Reference-oracle diff** (`tests/test_reference_oracle_diff.py`): the fast detector's deviation
   set diffed exactly against the independent reference detector over all 80 seeded fixture runs (40
   seeded-deviation, 40 clean), plus a structural guard that the reference implementation is not a
   renamed copy.
3. **Invariant checks** (`tests/test_invariants.py`): every flagged deviation across all 40 seeded
   runs names a real inject and a real step; time-to-detect and time-to-contain are never negative
   and, whenever computed, correspond to an action timestamp that actually exists in that run's log;
   40 of 40 seeded deviations are recalled and named correctly; 0 false flags over 40 clean runs.
4. **After-action tests** (`tests/test_after_action.py`): the success path (all 24 steps evidenced)
   marks all 24 exercised; the refusal path (one step's evidence deliberately withheld) marks that
   one step `not_exercised` and states why, without guessing; a step never performed at all is
   `not_exercised` regardless of evidence; the report covers exactly the 24 named steps.
5. **API tests** (`tests/test_api.py`), against a real (SQLite-backed) FastAPI `TestClient`, not a
   mocked service layer: scenario/inject listing shapes, run detail timing and deviations, 404 on a
   missing run, and the after-action report against the seeded fully-evidenced demo data.
6. **PostgreSQL fallback test** (`tests/test_postgres_fallback.py`): probes for a real reachable
   `INCIDENT_DATABASE_URL` and skips cleanly (not xfail, not a failure) when none is configured,
   which is the case on this machine; a second test confirms the default resolves to SQLite.
7. **The 40-run seeded-deviation benchmark and the 40-run clean-run false-flag benchmark**
   (`scripts/run_deviation_benchmark.py`, `docs/deviation_benchmark_output.txt`), the number-producing
   run behind the two headline claims, including the same reference-oracle diff over all 80 runs.
8. **The evidence-gate demonstration** (`scripts/run_evidence_gate_check.py`,
   `docs/evidence_gate_output.txt`), showing the refusal path and the success path against the same 6
   official runs in one recorded run.
9. **Intake unit and API tests** (`tests/test_intake_channels.py`, `test_intake_severity.py`,
   `test_intake_notification.py`, `test_intake_api.py`): channel normalization and the 3-channel
   equivalence property, the written severity matrix against hand-picked cases plus a 500-case
   reference-oracle diff (`@pytest.mark.parametrize`), the notification gate (unit and all 100
   seeded cases), and all 5 new routes against a real FastAPI `TestClient`.
10. **The intake benchmark** (`scripts/run_intake_benchmark.py`, `docs/intake_benchmark_output.txt`):
    the 100-case channel-normalization equivalence check, the 500-case severity-oracle diff, and the
    100-case notification-gate check, the number-producing run behind the three new headline claims.
11. **Vendor unit, oracle-diff and API tests** (`test_vendor_feeds.py`, `test_vendor_correlation.py`,
    `test_vendor_correlation_oracle_diff.py`, `test_vendor_severity.py`, `test_vendor_timing.py`,
    `test_vendor_containment_gate.py`, `test_vendor_api.py`): per-feed entity-shape checks, the
    25-chain/20-standalone correlation corpus diffed exactly against the independent union-find
    oracle, a 500-case severity-oracle diff over vendor-derived inputs, timing against the written
    playbook, the 100-case containment gate plus a full reversibility check, and all 8 new routes
    against a real FastAPI `TestClient`.
12. **The vendor benchmark** (`scripts/run_vendor_benchmark.py`, `docs/vendor_benchmark_output.txt`):
    the correlation corpus, the 500-case severity-oracle diff, and the 100-case containment gate with
    its reversibility check, the number-producing run behind the project's headline claims.

### `pytest -v` (38 tests, 37 passed, 1 skipped)

```
tests/test_after_action.py::test_success_path_marks_all_twenty_four_steps_exercised_when_all_are_evidenced PASSED
tests/test_after_action.py::test_refusal_path_never_marks_a_step_exercised_without_evidence PASSED
tests/test_after_action.py::test_a_step_never_performed_at_all_is_not_exercised_regardless_of_evidence PASSED
tests/test_after_action.py::test_report_covers_exactly_the_twenty_four_named_playbook_steps PASSED
tests/test_api.py::test_list_scenarios_returns_all_six_with_four_steps_and_five_injects_each PASSED
tests/test_api.py::test_list_injects_returns_all_thirty PASSED
tests/test_api.py::test_list_runs_returns_the_six_seeded_official_runs PASSED
tests/test_api.py::test_get_run_detail_reports_clean_timing_and_no_deviations PASSED
tests/test_api.py::test_get_missing_run_is_404 PASSED
tests/test_api.py::test_after_action_report_is_fully_exercised_from_the_seeded_demo_data PASSED
tests/test_detector.py::test_clean_run_has_no_deviations PASSED
tests/test_detector.py::test_missing_step_is_flagged_by_name PASSED
tests/test_detector.py::test_wrong_step_extra_action_is_flagged_by_name PASSED
tests/test_detector.py::test_unrecognized_action_with_no_step_id_is_flagged_as_wrong_step PASSED
tests/test_detector.py::test_out_of_order_is_flagged_naming_the_step_that_jumped_early PASSED
tests/test_detector.py::test_every_deviation_names_a_real_inject_and_step_that_exist PASSED
tests/test_injects.py (5 tests) PASSED
tests/test_invariants.py::test_every_flagged_deviation_names_a_real_inject_and_step_across_all_seeded_runs PASSED
tests/test_invariants.py::test_timing_is_never_negative_and_never_references_a_nonexistent_action_across_all_runs PASSED
tests/test_invariants.py::test_forty_of_forty_seeded_deviations_are_flagged_by_name PASSED
tests/test_invariants.py::test_zero_false_flags_over_forty_clean_runs PASSED
tests/test_postgres_fallback.py::test_schema_stands_up_against_real_postgres SKIPPED
tests/test_postgres_fallback.py::test_default_database_url_is_sqlite_when_no_postgres_url_is_configured PASSED
tests/test_reference_oracle_diff.py::test_primary_and_reference_agree_exactly_on_every_seeded_and_clean_run PASSED
tests/test_reference_oracle_diff.py::test_reference_oracle_is_not_a_renamed_copy PASSED
tests/test_scenarios.py (5 tests) PASSED
tests/test_timing.py (4 tests) PASSED

37 passed, 1 skipped in 0.73s
```

Full output: `backend/docs/test_output.txt`.

### Intake extension: `pytest -v` (full backend suite, 557 passed, 1 skipped)

Running the whole backend suite with the intake tests added (`docs/intake_test_output.txt`)
covers channel normalization and the 3-channel equivalence property, hand-picked severity
cases plus all 500 seeded cases diffed against the independent reference oracle
(`@pytest.mark.parametrize`, one assertion per case), the notification gate (unit cases plus
all 100 seeded cases), and all 5 new routes against a real FastAPI `TestClient`. The 1 skip
is the pre-existing PostgreSQL-fallback probe, unrelated to this extension.

### Vendor extension: `pytest -q` (full backend suite, 1076 passed, 1 skipped)

Running the whole backend suite with the vendor tests added (`docs/test_output.txt`) covers
per-feed entity-shape normalization, the 25-chain/20-standalone correlation corpus diffed
exactly against the independent union-find oracle, 500 seeded severity cases over vendor-derived
inputs diffed against the same reference oracle the intake extension uses, the written-playbook
timing calculation, the 100-case containment approval gate plus a full reversibility check, and
all 8 new routes against a real FastAPI `TestClient`. The 1 skip is the same pre-existing
PostgreSQL-fallback probe.

### Console: `npm run test` (15 tests, Vitest + Testing Library)

`api.test.ts` (mocked `fetch`, request shapes for all 5 API calls, error propagation on non-2xx),
`ScenarioTimeline.test.tsx` (empty state, injects grouped by scenario and ordered by timestamp),
`DeviationsPanel.test.tsx` (no-run prompt, no-deviations message for a clean run, step/run/type
naming for a flagged run), `AfterActionReport.test.tsx` (loading state, exercised vs not-exercised
lines with their reasons), `App.test.tsx` (initial load wiring, load-error surfacing). All 15 pass;
see Building and running for the command. Full output: `backend/docs/frontend_test_output.txt`.

## Findings

**The first honest run of the 40-seeded-deviation benchmark measured 38/40, not 40/40, and the
miss was a real bug in the fixture generator, not the detector.** Two `wrong_step` fixtures
(`seeded.016` and `seeded.034`) picked a "foreign" scenario using `(scenario_index + 1 + i // 3) % 6`,
which for those two values of `i` wrapped back to the run's *own* scenario. The "extra" action then
named a step that legitimately belonged to the run's own playbook, so `detect_deviations` correctly
saw a normal, non-foreign action and flagged nothing, exactly as it should for an action that is not
actually foreign. This is the measurement that discriminated: `run_deviation_benchmark.py` printed
`flagged=0 matched=0 -> MISS` for exactly those two runs, which pointed straight at the fixture, not
the detector, since every other `wrong_step` case (and every `missing_step` and `out_of_order` case)
passed on the same first run. The wrong hypothesis considered first was a detector edge case in the
"foreign step from another scenario" path; the fix was in `fixtures.py`'s offset arithmetic
(`offset = 1 + (i // 3) % (len(SCENARIOS) - 1)`, which is always in `1..5` and can never wrap back to
`0`), not in `detector.py`, which was correct throughout. After the fix, the same benchmark measured
40/40 on the next run, and the reference-oracle diff over all 80 runs (including the two previously
broken fixtures) matched exactly both before and after, because the reference detector was diffed
against whatever the fixtures actually contained, not against the intended ground truth directly.

**Everything else measured clean on the first real run.** The out-of-order deviation always names
the step that ran ahead of its expected turn (the "later" step in playbook order whose timestamp
came in earlier), not the step it jumped ahead of; an early hand-written unit test assumed the
opposite and was corrected to match the detector's (correct, and more useful for a responder reading
the report) convention rather than the other way around.

**Intake extension: all 3 benchmarks measured clean on the first real run, which is itself worth
stating rather than quietly accepting.** Channel normalization (100/100), the severity-oracle diff
(500/500) and the notification gate (100/100) all passed without a second attempt, unlike the
base harness's 38/40-then-fixed deviation benchmark above. The honest reason is scope, not extra
care: each of these three properties is checked by a single deterministic function with a small,
enumerable input space (3 booleans/enums for severity, one boolean for notification approval, one
equality check for channel normalization), so there was no sequencing or timing dimension for a
fixture-generator bug to hide in, which is exactly the dimension that produced the base harness's
real bug. Writing "measured clean" without this context would read as a suspiciously easy win; the
context is why it is not one.

**Vendor extension: the correlation and severity benchmarks measured clean on the first real run;
the containment-timing integration bug above (see Design deep-dives) is this extension's real find.**
25/25 chains, 500/500 severity cases and 100/100 gate decisions all passed without a second attempt,
for the same reason the intake benchmarks did: each is a deterministic function over a small,
enumerable input space with the sequencing risk isolated to the corpus generator, and the 25-chain
corpus was built deliberately (distinct hosts and users per chain, timestamps spread 500 minutes
apart) to avoid the base harness's own foreign-scenario-wraparound class of bug. The genuine
engineering miss was one layer up, at the API integration boundary where a derived timing field met
a request schema that had never been asked to carry a simulated-clock timestamp; see Design
deep-dives for the full symptom-to-fix account.

## Measured results

Machine: 8 physical / 16 logical cores, Windows 11 Home 10.0.26200, Python 3.12.10, Node.js
v22.17.1. Fixtures: 40 seeded-deviation runs (one deliberately seeded deviation each, ground truth
known), 40 clean runs, 6 official fully-evidenced demo runs, all built deterministically by
`incident_harness/fixtures.py`. Full raw output: `backend/docs/deviation_benchmark_output.txt` and
`backend/docs/evidence_gate_output.txt`.

| Claim | Measured | Met |
|---|---|---|
| 30 injects across 6 scenarios over a simulated utility IT estate | 30 injects, 5 per scenario, across 6 named scenarios (`incident_harness/injects.py`, `scenarios.py`) | Yes |
| Time to detect and time to contain measured per inject against a written playbook | `timing.compute_timing` measured on every run; never negative; `None` (not zero) when no matching action exists | Yes |
| 40 of 40 seeded playbook deviations flagged by name | **40/40** (measured 38/40 on the first attempt; root cause was a fixture-generator bug, not the detector; see Findings) | Yes |
| 0 false flags over 40 clean runs | **0** false flags over 40/40 clean runs, on the first attempt | Yes |
| After-action report refuses to mark any of 24 playbook steps exercised without a linked evidence artifact | Refusal path: 23/24 exercised, the withheld step named `not_exercised` with reason "no linked evidence artifact"; success path: 24/24 exercised | Yes |

**The one number to defend in an interview: 38/40 on the first attempt, not 40/40.** The honest
story is not that the detector needed tuning to hit the target, it is that the *fixture generator*
had an arithmetic bug that occasionally made a "foreign" step equal to the run's own scenario,
silently turning a seeded deviation into a non-deviation. The detector's own logic was correct in
both runs; the seeded ground truth was briefly wrong. `run_deviation_benchmark.py` and
`tests/test_invariants.py::test_forty_of_forty_seeded_deviations_are_flagged_by_name` both reflect
the corrected fixture and both pass at 40/40 as committed.

### Intake extension

Machine: Windows 11 Home 10.0.26200, Python 3.12.10. Full raw output: `backend/docs/intake_benchmark_output.txt`.

| Claim | Measured | Met |
|---|---|---|
| 3 incoming report channels (customer report, internal alert, researcher disclosure) normalized onto one incident record | **100/100** seeded cases normalized to identical `(data_sensitivity, scope, actively_exploited)` across all 3 channels | Yes |
| Severity classified against a written matrix checked by an independent oracle | **500/500** seeded cases matched the independent reference oracle, on the first attempt | Yes |
| Every customer notification held behind a named human approval | **100/100** seeded cases (50 without approval, 50 with named approval) matched the expected gate decision; 0 false sends, 0 false holds | Yes |

### Vendor extension

Machine: Windows 11 Home 10.0.26200, Python 3.12.10. Full raw output: `backend/docs/vendor_benchmark_output.txt`.

| Claim | Measured | Met |
|---|---|---|
| 4 vendor alert feeds (endpoint detection, email gateway, identity provider, managed-detection escalation) normalized onto one incident record | 120 seeded alerts (25 chains x 4 feeds + 20 standalone); **25/25** chains correctly folded to 1 incident each, **0/20** false groupings; primary vs. independent reference correlation engine exact agreement (45/45 incidents) | Yes |
| Severity classified against a written matrix matching an independently coded oracle on 500 of 500 cases | **500/500** seeded vendor-derived cases matched the independent reference oracle, on the first attempt | Yes |
| Time-to-detect and time-to-contain scored against a written playbook | `compute_vendor_timing` measured against `playbook.py`'s written detect/contain steps; `None` (not zero) when no matching action exists, confirmed by `test_vendor_timing.py` | Yes |
| Containment ran only behind a named approver; 100 of 100 gate decisions correct; 0 unapproved actions | **100/100** gate decisions correct (50 unapproved refused, 50 approved executed); **0** unapproved actions executed | Yes |
| Every action reversible | **50/50** executed actions successfully reverted to their pre-containment state (`undo_containment`, verified empirically, not assumed) | Yes |

## Building and running

Backend (Python 3.12, a virtualenv per repo):

```
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest -v                             # full suite incl. intake+vendor: 1076 passed, 1 skipped
venv\Scripts\python scripts\run_deviation_benchmark.py         # the 40+40-run deviation benchmark
venv\Scripts\python scripts\run_evidence_gate_check.py          # the after-action refusal/success demo
venv\Scripts\python scripts\run_intake_benchmark.py              # channel normalization, severity oracle, notification gate
venv\Scripts\python scripts\run_vendor_benchmark.py               # correlation corpus, severity oracle, containment gate
venv\Scripts\python scripts\init_db.py                            # stand up (and seed) the schema
venv\Scripts\python -m uvicorn incident_harness.api:app --port 8000   # serves the API on :8000
```

By default this runs against a local SQLite file (`backend/incident_harness.db`, regenerated by
`scripts/init_db.py` or by first running the API). To use PostgreSQL instead:

```
set INCIDENT_DATABASE_URL=postgresql://user:password@localhost:5432/incident_harness
```

Console (Node.js 18+):

```
cd frontend
npm install
npm run test          # 15 tests
npm run build          # tsc -b && vite build
npm run dev             # serves on :5173, proxies /api to :8000
```

## Sibling comparison

[`ai-governance-audit-readiness-register`](https://github.com/Manas103/ai-governance-audit-readiness-register)
shares this repo's "refuse and name the missing thing" mechanic: that register withholds an
audit-ready verdict the instant one of 12 control families has no evidence artifact, naming exactly
which ones; this harness withholds "exercised" status from a playbook step under the identical rule.
The register's correctness question collapses entirely to a set difference over a fixed 12-item
vocabulary (1,500/1,500 verdicts matched ground truth, 0 false-ready, because there is no sequencing
or timing dimension at all). This harness's correctness question is strictly harder because the
evidence-gate check is only one of three things the detector has to get right: it also has to
recover a step's *identity* (missing vs wrong) and its *relative order* (out of order) from a
timestamped action log, which is exactly the dimension that produced this repo's real bug (see
Findings) and that the register's simpler, order-free evidence model never has to face.

## Limitations

- **A run's "actions" are hand-entered or fixture-generated records, not ingested from a real EDR,
  SIEM, or ticketing system.** Nothing in this repo parses a real log format; `ResponderActionRow`
  is populated directly, so a production version would need a real ingestion adapter per source
  system, which is out of scope here.
- **Evidence is checked for presence and linkage, not for quality or actual review.**
  `EvidenceArtifact` only asks whether an artifact reference (a log path, a ticket id, a screenshot
  path) is attached to the (run, step) pair that performed it; it does not verify the artifact's
  contents actually substantiate the step, exactly the same gap the sibling register discloses for
  its own evidence model.
- **The out-of-order deviation type only detects violations of adjacent-pair ordering as
  detector.py defines it; it does not attempt to recover a full edit-distance-style diff of an
  arbitrarily scrambled sequence.** For the exercise's own 4-step playbooks, this is sufficient (and
  the reference oracle, using a different quadratic technique, agrees exactly on all 80 fixture
  runs), but a longer, more heavily reordered playbook could in principle need a more general
  sequence-alignment approach than either implementation here uses.
- **The live end-to-end backend-and-frontend integration (a running `uvicorn` process actually
  serving a running `npm run dev` console in one browser session) was not captured as an automated
  test in this build**, for the same reason the sibling repo's console tests are not: the console is
  proven against a mocked `fetch` and a real (in-process) FastAPI `TestClient`, not a bound network
  port, consistent with this build's process/port guard.
- **Intake extension.** The severity matrix and the notification gate are both small, enumerable
  rule checks (Findings explains why all 3 benchmarks measured clean on the first attempt, unlike
  the base harness's own deviation benchmark); a real triage function would weigh evidence the
  written matrix here does not model (customer tier, regulatory jurisdiction, prior incident
  history for the same account). `send_notification` checks that an approver is named, not that
  the name is a real, authorized person in any identity or role system, which this build does not
  have access to. No console UI was added for the intake endpoints; they are exercised by
  `tests/test_intake_api.py` against a real FastAPI `TestClient`, not a browser.
- **Vendor extension.** `EntityStateStore` is an in-memory stand-in for a live EDR/IdP/SOAR
  platform (see `containment.py`'s module docstring); nothing here calls a real vendor API, and
  `apply_containment`/`undo_containment` only decide and record what should happen, not execute it
  against a live system. The containment approval gate checks that an approver is *named*, the same
  limitation `send_notification` discloses above, not that the name is authorized in any real
  identity system. The 2-hour correlation window (`CORRELATION_WINDOW_MINUTES`) is a documented,
  inspectable constant tuned for this corpus's own narrative pacing, not validated against a labeled
  real-world alert-correlation dataset, since none exists for this synthetic domain. No console UI
  was added for the vendor endpoints either, for the same reason as the intake extension; they are
  exercised by `tests/test_vendor_api.py` against a real FastAPI `TestClient`.
