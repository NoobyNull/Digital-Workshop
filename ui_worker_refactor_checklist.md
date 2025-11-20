# Instructions (How to use this document)
1) Read this top-to-bottom before touching code; don7t skip sections.  
2) For any task you start, mark its checkbox, perform every sub-bullet beneath it, and add brief notes in your dev log.  
3) Do not change message/types or policies without updating the corresponding chapter text and schemas.  
4) After each chapter7s changes, run the listed tests/smokes before proceeding.  
5) If blocked or unsure, leave a note under the relevant bullet and stop-do not guess; ask for review.  
6) Keep the feature flag to fall back to legacy until Chapter 9 is complete and signed off.  
7) When you reopen this file, start at the first unchecked item in order; do not reorder steps without lead approval.

# UI/Worker Refactor Constitution (Checklist)

- [ ] **Preamble**  
  Keep the UI loop unblocked; put heavy work off-UI; ensure observability, cancellation, and recovery; require proof (tests/smokes) before merging each stage. This is the guiding principle: any step that risks blocking the UI must be redirected to the worker and proven safe.

- [ ] **Chapter 1 - Contract & Governance**  
  Define the language both sides speak and lock it down so everyone codes against one contract.
  - [ ] Message types enumerated and frozen: `load_request`, `load_progress`, `load_chunk`, `load_complete`, `timing_request`, `timing_result`, `error`, `cancel`, `heartbeat`, `shutdown`, `ack`, `busy/rejected`.
    - [ ] Each message includes `job_id`, `timestamp`, and `version`.
  - [ ] Payload schema for each message documented (fields, units, nullable rules, job_id correlation, ordering guarantees).
    - [ ] Document expected ordering (e.g., progress monotonic, chunk order).
  - [ ] Backward-compatibility plan (version field or feature flag) written down.
  - [ ] Single public interface: `GcodeJobRunner.load/cancel/status/shutdown`; no UI code references worker internals.
    - [ ] Public API docs for parameters, return values, and threading expectations.
  - [ ] Guards: forbid Qt objects/types in worker; forbid UI imports in worker; forbid VTK in worker.
    - [ ] Static check/lint rule added if possible.
  - [ ] Tests: schema round-trip (ser/deser), invalid payload rejection, static scan for forbidden imports, interface smoke (call API with stub worker).

- [ ] **Chapter 2 - Process Model**  
  Decide how the worker lives, dies, and restarts so UI stays responsive and predictable.
  - [ ] Worker creation policy: lazy spawn; record PID; expose "running/busy" state.
    - [ ] Store PID and start time for logs/diagnostics.
  - [ ] Single active job lock: reject/queue policy decided and documented; user feedback for "busy".
    - [ ] If rejecting, surface clear UI message; if queueing, show queue status.
  - [ ] Heartbeat: interval, grace period, timeout, and restart policy defined; heartbeat handler resets watchdog.
    - [ ] Heartbeat includes worker health snapshot (cpu/mem optional).
  - [ ] Auto-restart: on crash/hang, tear down IPC cleanly and respawn with fresh job queue cleared.
    - [ ] Ensure stale pipes/queues are discarded.
  - [ ] Clean shutdown: UI exit sends shutdown; worker drains/acknowledges (or times out and is killed).
  - [ ] State machine documented: Idle -> Busy -> Cancelling -> Idle; include transitions for crash/timeout.
    - [ ] Diagram or table in docs.
  - [ ] Tests: kill worker -> restart; inject hang -> timeout -> restart; load while busy -> policy honored; shutdown path closes without leaks.

- [ ] **Chapter 3 - Data Flow**  
  Specify what moves where, in what shape, and how to avoid choking the UI.
  - [ ] Loading/parsing: chunks include move batch, progress %, line numbers, and optional preview stats; end-of-stream marker defined.
    - [ ] Chunk schema includes min/max coordinates for quick bounds updates.
  - [ ] Chunk sizing/backpressure: max chunk size set; queue depth cap; policy on overflow (drop oldest/newest or backpressure) written.
    - [ ] Document impact on UI (e.g., possible coarse updates under pressure).
  - [ ] Timing: runs post-load in worker; handles feed overrides; emits partial/final metrics; handles zero/NaN safely.
    - [ ] Timing request message includes machine params and overrides.
  - [ ] Job IDs on every message; stale/out-of-order messages ignored on UI.
    - [ ] UI drops messages for unknown job_ids with debug log entry.
  - [ ] Tests: large file streamed incrementally; slow UI consumer simulated; timing results validated on known fixture; malformed G-code triggers error path with user-safe messaging.

- [ ] **Chapter 4 - UI Integration**  
  Wire the UI to consume worker output without blocking and with clear user feedback.
  - [ ] UI message pump is non-blocking (signals/async queue); no waits/sleeps on UI thread.
    - [ ] Central dispatcher handles routing and stale-job filtering.
  - [ ] Renderer updates are incremental; no full geometry rebuild per tick; cut/ahead colors and toolhead update off the streamed data.
    - [ ] Apply chunk deltas, not whole-scene redraws.
  - [ ] Controls policy: either disable while busy or auto-cancel existing job on new request; chosen policy enforced uniformly.
    - [ ] Buttons/menus reflect busy state; cursor/spinner optional.
  - [ ] Status UX: visible states for Loading/Cancelled/Failed/Completed; errors mapped to friendly text; stale-job messages ignored.
    - [ ] Status bar + dialog copy agreed and documented.
  - [ ] Tests: rotate/zoom during load remains smooth; Start -> Cancel -> Start works; file switch mid-load stops old job and starts new; controls enable/disable as expected.

- [ ] **Chapter 5 - Error Handling & Resilience**  
  Classify failures, message them well, and ensure recovery paths are deterministic.
  - [ ] Error taxonomy documented: validation, parse/runtime, timeout, worker crash, IPC failure; user messages and logs mapped per class.
    - [ ] Include remediation hints (e.g., "check file encoding").
  - [ ] Job IDs ensure stale deliveries are ignored; UI resets state on worker restart.
  - [ ] Logging policy: stack traces/log detail in logs only; user gets concise actionable error; sensitive data scrubbed.
  - [ ] Tests: bad file; forced parse exception; forced timeout; forced crash; injected stale messages; verify UI recovers and messaging is correct.

- [ ] **Chapter 6 - Performance & Limits**  
  Set and enforce bounds so heavy files don7t sink the app.
  - [ ] File size limits enforced early with user prompt; memory cap per job; CPU nice/affinity option documented.
    - [ ] Config defaults and override locations documented.
  - [ ] Configurable chunk size and queue depth; defaults picked to balance throughput vs. UI smoothness.
  - [ ] Benchmarks: load time, time-to-first-chunk, peak memory on large file; target thresholds recorded.
  - [ ] Tests: near-threshold warning; oversize fail-fast; run under resource cap; measure that UI frame rate does not drop under load.

- [ ] **Chapter 7 - Observability**  
  Make it debuggable: logs, metrics, and health signals.
  - [ ] Structured logs: job_id, pid, state transitions, errors, timings; log levels defined.
    - [ ] Log format sample added to docs.
  - [ ] Metrics (if enabled): counters (loads started/completed/cancelled/failed, restarts), timers (load duration, time-to-first-chunk, timing duration), gauges (queue depth).
    - [ ] Metrics names/units documented; toggle location noted.
  - [ ] Health indicator: surface heartbeat age and worker status in UI dev tools/logs.
  - [ ] Tests: sample run emits ordered transitions; metrics collected and non-zero where expected.

- [ ] **Chapter 8 - Testing Plan**  
  Spell out how we prove it works before declaring victory.
  - [ ] Unit: contract ser/deser; state machine transitions; cancel logic; heartbeat watchdog; chunk assembler.
    - [ ] Include fixtures for valid/invalid messages.
  - [ ] Integration: UI<->worker E2E for load/cancel/switch/crash; IPC reconnection after restart.
    - [ ] Mock slow consumer in UI to test backpressure.
  - [ ] Manual smoke: rotate/zoom during load; tweak colors; playback while worker idle; intentional load error UX; simulate unplugging/killing worker.
  - [ ] CI hooks: add targeted integration job to prevent regression on IPC/worker path.

- [ ] **Chapter 9 - Rollout & Backout**  
  Plan the controlled release and the escape hatch.
  - [ ] Feature flag gates new worker path; legacy path kept initially.
    - [ ] Flag name and config surface documented.
  - [ ] Migration steps spelled out: wrap API -> move load to worker -> move timing -> remove old threads/logic -> retire flag.
  - [ ] Backout: toggle flag to legacy, revert worker spawn, documented rollback steps and configs.

- [ ] **Appendix - Dev Ergonomics**  
  Make it easy to develop, debug, and reproduce.
  - [ ] Local dev helpers: script to start worker standalone; log tail command; debug mode with verbose IPC tracing.
  - [ ] Failure repro notes: how to simulate hang/crash/oversize; sample G-code fixtures for tests.
  - [ ] Documentation updated in README/CONTRIBUTING for new workflow and flags.
