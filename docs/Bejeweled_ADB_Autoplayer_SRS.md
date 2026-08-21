# Software Requirements Specification

## Wireless-ADB Strategic Match-3 Autoplayer

**Document version:** 1.0
**Date:** 2026-08-11
**Status:** Implementation baseline
**Target implementer:** Autonomous or agentic software-development system
## 1. Purpose

This document specifies a PC-side application that autonomously plays an existing Bejeweled-style match-3 game on an Android phone connected through wireless Android Debug Bridge (ADB).

The application shall:

- observe the unmodified game through screenshots;
- recognise an animated 8×8 gem board;
- distinguish gem identity from transient visual effects;
- detect stable, moving, transitional, and exceptional game states;
- model swaps, matches, gravity, cascades, special-gem creation and activation;
- plan multiple moves ahead to deliberately create and combine special gems;
- execute swipes through ADB;
- detect level completion and resume on the reset board;
- fail safely when observation or simulation confidence is insufficient;
- retain evidence needed to diagnose recognition and decision errors.

The initial target is one game, one phone model/resolution, and one visual theme. Portability shall be provided through configuration rather than required for the first release.

## 2. Scope

### 2.1 In scope

- PC-side Python application.
- Wireless ADB connection to one authorised Android device.
- Portrait game at the observed 720×1536 screenshot resolution.
- Fixed 8×8 match-3 board.
- Recognition of ordinary gems and visually modified/special gems.
- Temporal handling of sparkle, glow, selection, hint, explosion and movement effects.
- Legal move generation and board simulation.
- Strategic search over multiple turns.
- Replanning after every executed move.
- Progress-bar, score, level and board-reset observation.
- Level-transition handling without advertisements.
- Offline replay and regression testing from captured screenshots/video frames.
- Human-readable and machine-readable logs.

### 2.2 Out of scope for version 1

- Modifying, instrumenting or reverse-engineering the game APK.
- Reading game process memory.
- Rooting the phone.
- Bypassing anti-cheat or platform security controls.
- Supporting arbitrary match-3 games or arbitrary screen resolutions without calibration.
- Competitive leaderboard optimisation.
- Remote control of more than one phone.
- Automatically dismissing advertisements, purchases or account dialogs.
- General-purpose visual-language-model control during the real-time loop.

### 2.3 Operating assumption

The user owns or is authorised to control the device and accepts that automated play may violate the game publisher's terms. The implementation shall not conceal automation or attempt to defeat anti-automation mechanisms.

## 3. Observed target-game characteristics

The following facts are derived from the supplied screenshots and are treated as the initial calibration baseline:

| Characteristic | Observed value |
|---|---|
| Orientation | Portrait |
| Screenshot size | 720×1536 px |
| Board | 8 columns × 8 rows |
| Approximate board left/right | x=0 / x=720 |
| Approximate board top/bottom | y=320 / y=1005 |
| Approximate cell width | 90 px |
| Approximate cell height | 85–86 px |
| Ordinary visual classes | Red, green, blue, yellow, purple, orange, white/silver |
| Score | Upper-left, persistent |
| Level indicator | Upper-right, e.g. `Level 2` |
| Level progress | Horizontal bar directly below board |
| Board reset | Occurs after level point requirement is completed |
| Advertisements | None in the normal play loop |

Approximate geometry shall be stored in configuration and validated at startup. It shall not be duplicated as unexplained numeric constants in processing code.

## 4. Unknown game rules requiring calibration

The implementation agent shall not silently invent the following rules. It shall represent them as explicit configuration, test data or unresolved calibration items:

1. Exact patterns that create each special gem.
2. Whether the swapped gem, match centre or another position receives the created special.
3. Special-gem activation rules and blast geometry.
4. Effects of swapping two special gems.
5. Whether special gems activate when matched, swapped, hit by another special, or any combination.
6. Score awarded for matches, cascades, special creation and special activation.
7. Whether unused special gems provide a level-end bonus.
8. Whether the glowing white gem in the supplied screenshot is an idle effect, hint, selection, special state or activation state.
9. Refill distribution and whether gem generation avoids immediate matches.
10. Whether later levels introduce blockers, holes, alternative board masks, timers or new gem types.
11. Exact relationship between the progress bar, displayed score and target level score.

Unknown rules shall be isolated behind a `RuleSet` interface. The first functional milestone may use documented assumptions, but every assumption shall be named in configuration and emitted in the run metadata.

## 5. Definitions

| Term | Definition |
|---|---|
| Cell | One logical location on the 8×8 board. |
| Gem identity | Stable semantic class such as red, blue or white. |
| Effect | Transient or persistent overlay such as sparkle, glow, selection or explosion. |
| Stable board | A board whose classified cells and positions remain consistent for the configured temporal window. |
| Settled board | A stable board with no falling gems, active removals or unresolved cascades. |
| Ply | One simulated player swap. |
| Refill | New, previously invisible gems entering after gravity. |
| Plan | Ranked sequence of simulated moves; only its first move is executed. |
| Confidence | Normalised value from 0.0 to 1.0 representing observation reliability. |
| Deterministic region | Simulation before unknown refill affects an outcome. |

## 6. System context

The system consists of the following logical components:

1. **ADB transport** — discovers the selected device, captures screenshots and issues swipes.
2. **Frame processor** — decodes frames, normalises orientation and extracts regions of interest.
3. **Board recogniser** — classifies gem identities, effects, occupancy and confidence.
4. **Game-state controller** — determines whether play is safe and coordinates all transitions.
5. **Rule engine** — simulates swaps, matches, gravity, cascades and specials.
6. **Strategic planner** — searches candidate moves and estimates uncertain refills.
7. **Action executor** — converts logical moves to safe physical swipes.
8. **Outcome verifier** — compares predicted and observed results and triggers model correction or recovery.
9. **Recorder** — stores frames, boards, decisions, timings and errors.
10. **Calibration utility** — derives geometry, templates, colour models and thresholds from labelled samples.

The core recogniser, simulator and planner shall not invoke ADB directly. Hardware I/O shall be restricted to transport and action interfaces so that recorded sessions can be replayed deterministically.

## 7. Operating modes

### 7.1 Live autonomous mode

The application observes, plans and executes moves until stopped or a terminal error occurs.

### 7.2 Observe-only mode

The application captures and classifies the game but never sends input. It shall display or log the inferred game state, board, effects and confidence.

### 7.3 Suggest-only mode

The application calculates and displays the preferred move and alternatives but does not execute them.

### 7.4 Replay mode

The application processes a recorded frame sequence without a connected device. Timing may run at real time or as fast as possible.

### 7.5 Simulation mode

The planner accepts a symbolic board and configured rule set without image recognition or ADB.

### 7.6 Calibration mode

The application records representative frames, allows cell/effect labelling, and produces versioned recognition parameters.

## 8. Functional requirements

### 8.1 Configuration and startup

- **FR-CFG-001:** The application shall load configuration from a version-controlled YAML or TOML file.
- **FR-CFG-002:** Configuration shall include device selector, expected orientation, screenshot dimensions, board geometry, cell sampling regions, UI regions, thresholds, timings, rule-set identifier and planner limits.
- **FR-CFG-003:** Command-line arguments may override configuration values and shall be recorded in run metadata.
- **FR-CFG-004:** Startup shall validate configuration schema and reject unknown or invalid values with actionable messages.
- **FR-CFG-005:** The application shall support deterministic random seeds for refill sampling and tests.
- **FR-CFG-006:** Startup shall perform a dry connection, capture one frame, verify resolution/orientation and locate the board before enabling input.
- **FR-CFG-007:** Live input shall remain disabled until the user explicitly selects autonomous mode.

### 8.2 ADB transport

- **FR-ADB-001:** The application shall list connected ADB devices and require an unambiguous target.
- **FR-ADB-002:** The target may be selected by serial/IP:port in configuration or CLI.
- **FR-ADB-003:** The application shall capture lossless PNG screenshots using ADB or an equivalently authorised ADB-backed stream.
- **FR-ADB-004:** Screenshot acquisition shall have configurable timeout and retry limits.
- **FR-ADB-005:** The application shall execute adjacent-cell swipes with configurable duration.
- **FR-ADB-006:** It shall never swipe outside the calibrated board in autonomous mode.
- **FR-ADB-007:** It shall suppress duplicate action submission until the preceding action has been observed or timed out.
- **FR-ADB-008:** On disconnection, the controller shall enter `DISCONNECTED`, cease input and attempt only the configured bounded reconnection policy.
- **FR-ADB-009:** All ADB commands, durations, exit codes and relevant error output shall be logged without leaking unrelated host information.

### 8.3 Frame acquisition and preprocessing

- **FR-VIS-001:** Each frame shall receive a monotonic timestamp and unique identifier.
- **FR-VIS-002:** Processing shall validate frame dimensions and orientation.
- **FR-VIS-003:** The board, score, level and progress-bar regions shall be extracted from configurable geometry.
- **FR-VIS-004:** The application shall support temporal bursts of at least 3–5 frames over a configurable 300–600 ms window.
- **FR-VIS-005:** It shall calculate per-cell temporal statistics, including median image, colour stability and pixel-change ratio.
- **FR-VIS-006:** It shall retain the original frame for diagnostics rather than retaining only transformed crops.
- **FR-VIS-007:** Preprocessing may normalise brightness and colour, but raw and normalised data shall not be confused in logs or tests.

### 8.4 Board geometry

- **FR-GEO-001:** The initial implementation shall support an 8×8 rectangular grid.
- **FR-GEO-002:** Logical coordinates shall use zero-based `(row, column)` indexing.
- **FR-GEO-003:** Logical-to-screen conversion shall use calibrated cell centres and shall be unit-tested.
- **FR-GEO-004:** Startup shall validate expected grid borders or cell structure with a confidence metric.
- **FR-GEO-005:** If board geometry confidence falls below threshold, input shall be inhibited.
- **FR-GEO-006:** Geometry shall permit future board masks and non-playable cells without redesigning the board model.

### 8.5 Gem and effect recognition

- **FR-REC-001:** The recogniser shall classify every playable cell into a gem identity, `EMPTY`, or `UNKNOWN`.
- **FR-REC-002:** Gem identity and visual effect shall be separate fields.
- **FR-REC-003:** Initial ordinary identities shall include `RED`, `GREEN`, `BLUE`, `YELLOW`, `PURPLE`, `ORANGE`, and `WHITE`.
- **FR-REC-004:** Initial effect values shall include `NONE`, `SPARKLE`, `GLOW`, `SELECTED`, `HINT`, `MOVING`, `EXPLODING`, `SPECIAL_UNKNOWN`, and `UNKNOWN`.
- **FR-REC-005:** Recognition shall combine at least two independent feature families, such as colour and shape/template.
- **FR-REC-006:** Constant animation shall be handled through temporal aggregation, not by assuming pixel stability.
- **FR-REC-007:** Each cell result shall include identity confidence, effect confidence and evidence/source features.
- **FR-REC-008:** The board result shall include aggregate confidence and a list of ambiguous cells.
- **FR-REC-009:** A single low-confidence cell shall prevent autonomous input unless resolved by recapture or an explicitly configured conservative policy.
- **FR-REC-010:** The recogniser shall expose debug crops and overlays showing grid, labels and confidence.
- **FR-REC-011:** Classification thresholds and templates shall be versioned as a recogniser profile.
- **FR-REC-012:** The recogniser shall not use score or planner expectations to overwrite direct visual evidence. Expectations may be used only to flag inconsistencies.

### 8.6 Board stability and temporal state

- **FR-STB-001:** A board shall be considered stable only after its identities are consistent across a configurable number of frames.
- **FR-STB-002:** Sparkle/glow pixels shall not by themselves make a gem unstable when identity remains consistent.
- **FR-STB-003:** Falling, swapping, disappearing or newly appearing gems shall make the board unsettled.
- **FR-STB-004:** Stability evaluation shall use both symbolic classification and pixel-motion measures.
- **FR-STB-005:** The controller shall impose a minimum quiet period after a swipe before accepting a settled board.
- **FR-STB-006:** If a board does not settle within the configured maximum, the system shall enter recovery rather than issue another move.

### 8.7 Game-state controller

The controller shall support at least these states:

```text
STARTING
DISCONNECTED
LOCATING_BOARD
OBSERVING
BOARD_MOVING
BOARD_READY
PLANNING
ACTION_PENDING
VERIFYING_RESULT
LEVEL_ENDING
TRANSITIONING
NEW_LEVEL
RECOVERING
PAUSED
STOPPED
ERROR
```

- **FR-FSM-001:** Every input action shall be authorised by the state controller.
- **FR-FSM-002:** Swipes shall be permitted only from `BOARD_READY` after a successful plan.
- **FR-FSM-003:** State transitions shall have explicit predicates, timeouts and log events.
- **FR-FSM-004:** Unexpected UI or low confidence shall transition to `RECOVERING` or `PAUSED`, never directly to another swipe.
- **FR-FSM-005:** Manual stop shall inhibit further input immediately.
- **FR-FSM-006:** The latest state, reason and elapsed duration shall be visible in terminal/status output.

### 8.8 Score, level and progress recognition

- **FR-UI-001:** The application shall estimate level progress from the configured bar region.
- **FR-UI-002:** Progress shall be expressed as a confidence-bearing fraction from 0.0 to 1.0.
- **FR-UI-003:** The application shall recognise the displayed level number using OCR or template matching.
- **FR-UI-004:** Score recognition is recommended for verification but shall not block play if board and level state are reliable.
- **FR-UI-005:** OCR results shall be temporally filtered to prevent one-frame misreads.
- **FR-UI-006:** UI recognition shall tolerate background imagery behind the text by using local templates, thresholding or multiple frames.

### 8.9 Level completion and reset

- **FR-LVL-001:** Level completion shall be detected using multiple signals rather than a single pixel threshold.
- **FR-LVL-002:** Candidate signals shall include near-full progress, level-text change, loss of stable grid, global board motion, completion overlays and appearance of a new stable board.
- **FR-LVL-003:** Upon detecting `LEVEL_ENDING`, the application shall cease swipes.
- **FR-LVL-004:** During `TRANSITIONING`, it shall observe without planning or input.
- **FR-LVL-005:** A new level shall be confirmed only when level identity and a complete stable board are observed consistently.
- **FR-LVL-006:** Strategic plans, predicted cascades and board-history comparisons shall reset at new-level confirmation.
- **FR-LVL-007:** Long-lived statistics, recognition profile and session score history shall not reset.
- **FR-LVL-008:** If the level number cannot be read, a board reset may still be inferred, but the event shall be marked `level_identity_uncertain`.
- **FR-LVL-009:** Near completion, the planner shall use a configurable end-of-level policy: `IMMEDIATE_POINTS`, `CREATE_SPECIALS`, or `DEFAULT`.

### 8.10 Rule engine and board simulation

- **FR-SIM-001:** The rule engine shall be pure and deterministic for a given board, move, rule set and refill sequence.
- **FR-SIM-002:** It shall enumerate all orthogonally adjacent swaps.
- **FR-SIM-003:** It shall reject moves that do not produce an allowed effect under the configured rules.
- **FR-SIM-004:** It shall find horizontal and vertical matches without double-counting intersecting structures.
- **FR-SIM-005:** It shall resolve simultaneous matches according to configured precedence.
- **FR-SIM-006:** It shall create special gems according to pattern, swap direction and placement rules.
- **FR-SIM-007:** It shall activate special gems and combinations according to the selected `RuleSet`.
- **FR-SIM-008:** It shall apply removals, gravity and refill repeatedly until settled.
- **FR-SIM-009:** It shall expose each intermediate cascade step for explanation and testing.
- **FR-SIM-010:** Unknown refills shall be supplied by an injectable refill provider.
- **FR-SIM-011:** Refill providers shall include deterministic sequence, seeded distribution and empirical distribution variants.
- **FR-SIM-012:** Simulation output shall include points estimate, created specials, activated specials, cascade depth, final board and uncertainty metadata.
- **FR-SIM-013:** Symbolic invariants shall be checked in debug/test mode: valid dimensions, allowed identities, no unresolved matches on a settled board unless rules permit them, and conservation consistent with refill count.

### 8.11 Strategic planning

- **FR-PLN-001:** The planner shall evaluate every legal immediate move.
- **FR-PLN-002:** It shall support a configurable search depth of at least 1–5 plies.
- **FR-PLN-003:** Initial multi-turn search shall use beam search with configurable beam width, defaulting to a practical range of 50–200 states.
- **FR-PLN-004:** Only the first move of the selected plan shall be executed.
- **FR-PLN-005:** The complete search shall be repeated after each observed settled board.
- **FR-PLN-006:** Transposition detection shall merge equivalent board states reached through different sequences when rule semantics allow.
- **FR-PLN-007:** Search shall obey a configurable wall-clock budget.
- **FR-PLN-008:** If the budget expires, the best completely evaluated immediate move may be used if confidence exceeds threshold.
- **FR-PLN-009:** Refill uncertainty shall be represented through sampled outcomes, expected values, risk penalties or a combination.
- **FR-PLN-010:** The planner shall distinguish deterministic pre-refill consequences from speculative post-refill consequences.
- **FR-PLN-011:** It shall produce a ranked list of moves with score components and principal variation.
- **FR-PLN-012:** Tie-breaking shall be deterministic when using the same random seed.
- **FR-PLN-013:** The planner shall support an optional fallback to a safe legal move when deeper search fails.

### 8.12 Evaluation heuristic

The heuristic shall be configurable and decompose its result into named terms. It shall support at least:

- immediate match value;
- expected cascade value;
- four-gem special creation;
- five-gem special creation;
- T/L special creation;
- special activation;
- special-special combination opportunity;
- preservation or destruction of existing specials;
- one-move setup potential;
- two-move setup potential;
- board mobility/number of legal moves;
- dead-board risk;
- refill uncertainty/risk;
- progress-to-level-end policy;
- discrepancy penalty when simulated mechanics are not well calibrated.

- **FR-EVL-001:** Heuristic weights shall be loaded from configuration.
- **FR-EVL-002:** Each decision record shall contain the contribution of every non-zero heuristic term.
- **FR-EVL-003:** Strategic setup rewards shall not exceed guaranteed level-completing value unless configured.
- **FR-EVL-004:** The implementation shall provide a baseline immediate-score heuristic for comparison.
- **FR-EVL-005:** Weight tuning shall operate on recorded games without requiring live-device play.

### 8.13 Action execution

- **FR-ACT-001:** A logical move shall contain source cell and destination adjacent cell.
- **FR-ACT-002:** Screen endpoints shall be calculated from cell-centre geometry.
- **FR-ACT-003:** Swipe duration and endpoint inset shall be configurable.
- **FR-ACT-004:** Immediately before a swipe, the controller shall verify that the current stable board matches the board used for planning.
- **FR-ACT-005:** If the board changed, the action shall be cancelled and replanned.
- **FR-ACT-006:** Every action shall have a unique identifier linking pre-action frame, board, plan, command and outcome.
- **FR-ACT-007:** The executor shall rate-limit inputs and permit at most one outstanding action.

### 8.14 Outcome verification and model adaptation

- **FR-VER-001:** After a swipe, the application shall wait for motion and then for a settled board.
- **FR-VER-002:** It shall compare observed post-move state to deterministic and sampled predicted outcomes.
- **FR-VER-003:** It shall classify discrepancies as recognition error, action-not-accepted, unknown rule, unexpected refill, transition, or unresolved.
- **FR-VER-004:** If no change occurs, one retry may be permitted only after confirming the pre-action board remains stable and the retry policy allows it.
- **FR-VER-005:** The system shall never retry blindly during movement or transition.
- **FR-VER-006:** Rule-learning suggestions may be generated from discrepancies but shall not silently modify production rules during a live run.
- **FR-VER-007:** Repeated discrepancies beyond threshold shall pause autonomous play.

### 8.15 Recovery

- **FR-RCV-001:** Recovery shall begin with observation-only recapture.
- **FR-RCV-002:** Recovery may wait, recapture, relocate the board, reconnect ADB or request operator intervention.
- **FR-RCV-003:** Recovery shall not press arbitrary UI controls.
- **FR-RCV-004:** A bounded retry counter shall prevent infinite recovery loops.
- **FR-RCV-005:** On terminal recovery failure, the application shall save diagnostic evidence and stop safely.

### 8.16 Recording and diagnostics

- **FR-LOG-001:** Each run shall have a unique session directory.
- **FR-LOG-002:** Logs shall include configuration hash, software version, recogniser profile, rule-set version, random seed and target device identifier.
- **FR-LOG-003:** Structured events shall use JSON Lines.
- **FR-LOG-004:** The system shall record state changes, captured frames, recognised boards, ambiguity, candidate moves, chosen move, swipe command, observed outcome, errors and timings.
- **FR-LOG-005:** Frame retention shall be configurable: all frames, decision frames, errors only, or none.
- **FR-LOG-006:** A diagnostic renderer shall produce an annotated image with grid coordinates, identity, effect and confidence.
- **FR-LOG-007:** The system shall export a concise session summary including levels completed, moves, recognition failures, average decision latency and special gems created/activated.

## 9. Data model

The following conceptual types shall be implemented with typed Python structures such as dataclasses, enums and immutable tuples where appropriate.

```python
GemType = RED | GREEN | BLUE | YELLOW | PURPLE | ORANGE | WHITE |
          SPECIAL_1 | SPECIAL_2 | SPECIAL_3 | EMPTY | UNKNOWN

EffectType = NONE | SPARKLE | GLOW | SELECTED | HINT | MOVING |
             EXPLODING | SPECIAL_UNKNOWN | UNKNOWN

CellObservation:
    row: int
    column: int
    gem_type: GemType
    effect: EffectType
    identity_confidence: float
    effect_confidence: float
    feature_summary: dict
    frame_ids: tuple[str, ...]

BoardObservation:
    cells: tuple[tuple[CellObservation, ...], ...]
    board_confidence: float
    stable: bool
    timestamp: float
    geometry_profile: str
    recognizer_profile: str

Move:
    source: Coordinate
    destination: Coordinate

SimulationResult:
    initial_board: BoardState
    move: Move
    cascade_steps: tuple[CascadeStep, ...]
    final_board: BoardState
    created_specials: tuple[SpecialEvent, ...]
    activated_specials: tuple[SpecialEvent, ...]
    estimated_points: float
    refill_count: int
    uncertainty: float

PlanCandidate:
    first_move: Move
    principal_variation: tuple[Move, ...]
    total_value: float
    score_components: dict[str, float]
    deterministic_depth: int
    sampled_outcomes: int
    risk: float
```

Observed board state and simulated board state shall be distinct types. Conversion shall be explicit and permitted only above the configured confidence threshold.

## 10. External interfaces

### 10.1 Command-line interface

Minimum commands:

```text
autoplayer devices
autoplayer calibrate --device <serial>
autoplayer observe --config <file>
autoplayer suggest --config <file>
autoplayer play --config <file>
autoplayer replay --session <path>
autoplayer simulate --board <file> --rules <file>
autoplayer render-debug --frame <file>
```

All live commands shall clearly display whether input is enabled.

### 10.2 Configuration interface

Recommended sections:

```yaml
device: {}
capture: {}
geometry: {}
recognition: {}
stability: {}
ui_detection: {}
rules: {}
planner: {}
action: {}
recovery: {}
logging: {}
```

### 10.3 Internal interfaces

```python
class FrameSource:
    def capture(self) -> Frame: ...


class BoardRecognizer:
    def recognize(self, frames: Sequence[Frame]) -> BoardObservation: ...


class GameStateDetector:
    def detect(self, observations: ObservationBundle) -> GameStateEvidence: ...


class RuleSet:
    def legal_moves(self, board: BoardState) -> Sequence[Move]: ...
    def simulate(
        self, board: BoardState, move: Move, refill: RefillProvider
    ) -> SimulationResult: ...


class Planner:
    def plan(self, context: PlanningContext) -> PlanResult: ...


class ActionSink:
    def swipe(self, move: Move, geometry: BoardGeometry) -> ActionReceipt: ...
```

## 11. Non-functional requirements

### 11.1 Performance

- **NFR-PERF-001:** On the target PC, ordinary stable-board recognition should complete within 500 ms after the temporal frame window is available.
- **NFR-PERF-002:** Default planning shall complete within 2 s; the maximum budget shall be configurable.
- **NFR-PERF-003:** The system shall sustain continuous play despite wireless ADB latency of approximately 0.5–2 s per decision cycle.
- **NFR-PERF-004:** Search shall degrade gracefully by reducing samples or depth rather than violating the input-safety rules.

### 11.2 Reliability and safety

- **NFR-REL-001:** No swipe shall occur when the board is moving, transitioning, missing or below the configured confidence threshold.
- **NFR-REL-002:** A process crash shall leave the phone untouched after the last completed ADB command.
- **NFR-REL-003:** Restart shall not assume the previous board or level state.
- **NFR-REL-004:** All timeouts and retry counts shall be finite.
- **NFR-REL-005:** Ctrl+C/manual stop shall halt new input immediately and exit cleanly.

### 11.3 Maintainability

- **NFR-MNT-001:** Vision, rules, planning, ADB and orchestration shall be separate packages with one-directional dependencies.
- **NFR-MNT-002:** Public functions and non-obvious algorithms shall be documented.
- **NFR-MNT-003:** Static type checking and linting shall run in CI.
- **NFR-MNT-004:** Rule and recogniser profiles shall have explicit schema versions.
- **NFR-MNT-005:** No production module shall depend on test fixtures.

### 11.4 Testability and reproducibility

- **NFR-TST-001:** Recognition and planning shall run without a connected phone.
- **NFR-TST-002:** Recorded inputs, configuration and seed shall reproduce a decision.
- **NFR-TST-003:** Every defect fixed from a captured session shall add a regression test when practical.
- **NFR-TST-004:** Golden test artefacts shall declare the profile and rule-set versions that produced them.

### 11.5 Security and privacy

- **NFR-SEC-001:** The application shall execute ADB commands through argument arrays rather than an interpolated shell.
- **NFR-SEC-002:** Device selectors and file paths shall be validated.
- **NFR-SEC-003:** The application shall not collect unrelated phone content.
- **NFR-SEC-004:** Screenshot/session retention shall be explicit and configurable.
- **NFR-SEC-005:** No network service shall listen by default.

## 12. Recommended implementation architecture

```text
src/autoplayer/
  cli.py
  config.py
  domain/
    board.py
    move.py
    observation.py
    events.py
  adb/
    transport.py
    capture.py
    input.py
  vision/
    geometry.py
    preprocessing.py
    features.py
    classifier.py
    temporal.py
    ui.py
    debug_render.py
  game/
    rules.py
    matching.py
    specials.py
    gravity.py
    refill.py
    simulator.py
  planning/
    heuristic.py
    beam_search.py
    uncertainty.py
    transposition.py
  controller/
    states.py
    state_machine.py
    recovery.py
    verifier.py
  recording/
    event_log.py
    session.py
    replay.py
  calibration/
    capture_samples.py
    label_samples.py
    build_profile.py
tests/
  unit/
  integration/
  replay/
  fixtures/
config/
  target_720x1536.yaml
  rules_initial.yaml
```

Recommended technologies:

- Python 3.12 or newer.
- OpenCV for image processing.
- NumPy for frame and board calculations.
- Pydantic or equivalent for configuration validation.
- Typer or argparse for CLI.
- pytest for tests.
- JSON Lines for events.

A machine-learning framework is not required initially. Introduce one only if labelled replay data demonstrates that engineered temporal colour/shape/template features cannot meet recognition acceptance criteria.

## 13. Planning algorithm baseline

### 13.1 Immediate move generation

For each cell, attempt swaps only to the right and down to enumerate each adjacent pair once. The rule engine determines legality.

### 13.2 Beam search

At depth zero, expand all legal moves. For each resulting state:

1. resolve deterministic effects;
2. sample refill outcomes when required;
3. calculate expected and risk-adjusted value;
4. add strategic board-pattern features;
5. retain the highest-valued unique states up to beam width;
6. repeat until depth or time budget is reached.

Recommended initial defaults:

| Parameter | Initial value |
|---|---:|
| Maximum depth | 3 plies |
| Beam width | 100 |
| Refill samples per uncertain node | 20 |
| Planning budget | 1.5 s |
| Risk policy | Expected value with configurable variance penalty |

### 13.3 Strategic patterns

The evaluator shall detect at least:

- one-swap four-in-a-row opportunities;
- one-swap five-in-a-row opportunities;
- T/L completion opportunities;
- patterns that can be completed after one preparatory move;
- special gems separated by one useful move;
- moves that destroy one of the above patterns.

Pattern evaluation shall operate on symbolic boards, not pixels.

### 13.4 Receding horizon

The planner may construct a multi-move plan, but the controller shall execute exactly one move before observing again. This requirement is mandatory because cascades and off-screen refills make long sequences uncertain.

## 14. State-transition requirements

| Current state | Condition | Next state | Action |
|---|---|---|---|
| `STARTING` | Device ready | `LOCATING_BOARD` | Capture initial burst |
| `LOCATING_BOARD` | Geometry confirmed | `OBSERVING` | Begin temporal classification |
| `OBSERVING` | Board moving | `BOARD_MOVING` | Wait |
| `OBSERVING` | Stable complete board | `BOARD_READY` | Freeze planning snapshot |
| `BOARD_READY` | Confidence sufficient | `PLANNING` | Search |
| `PLANNING` | Valid best move and board unchanged | `ACTION_PENDING` | Issue one swipe |
| `ACTION_PENDING` | Motion observed | `BOARD_MOVING` | Await settlement |
| `BOARD_MOVING` | Stable board observed | `VERIFYING_RESULT` | Compare outcome |
| `VERIFYING_RESULT` | Normal outcome | `BOARD_READY` | Replan |
| Any play state | Completion evidence | `LEVEL_ENDING` | Disable input |
| `LEVEL_ENDING` | Board/UI transition starts | `TRANSITIONING` | Observe only |
| `TRANSITIONING` | New stable board/level | `NEW_LEVEL` | Reset transient plan |
| `NEW_LEVEL` | Confirmation window passed | `BOARD_READY` | Resume |
| Any active state | ADB loss | `DISCONNECTED` | Disable input |
| Any active state | Repeated uncertainty | `RECOVERING` | Bounded recovery |
| Any state | Manual stop | `STOPPED` | No further input |

## 15. Testing requirements

### 15.1 Unit tests

Unit tests shall cover:

- coordinate conversion and grid bounds;
- match detection for horizontal, vertical, intersecting and simultaneous matches;
- legal/illegal swaps;
- gravity and refill order;
- each known special-creation pattern;
- each known special activation and combination;
- cascade termination;
- deterministic simulation under a fixed refill sequence;
- strategic pattern feature extraction;
- heuristic decomposition;
- beam-width and time-budget behaviour;
- state-machine valid and invalid transitions;
- progress-bar measurement on synthetic images;
- temporal identity stability despite animated overlays.

### 15.2 Golden-image recognition tests

The test corpus shall include:

- each ordinary gem in each board location where lighting/background differs materially;
- glow and sparkle phases across multiple frames;
- selected and hinted gems;
- gems in motion;
- explosion frames;
- stable boards;
- transition frames;
- new-level boards;
- low-confidence or corrupted captures.

Expected labels shall cover identity, effect and stable/unstable status.

### 15.3 Simulator property tests

Property-based tests should verify:

- only adjacent cells are swapped;
- board dimensions remain valid;
- gravity leaves no empty playable cell below an occupied cell after settlement;
- cascade processing terminates under bounded deterministic fixtures;
- generated legal moves satisfy rule definitions;
- equivalent seeded runs produce equivalent results.

### 15.4 Replay integration tests

Replay tests shall verify complete state sequences from pre-move board through swipe-equivalent event, animation, settlement and level transition. They shall not require ADB.

### 15.5 Live-device tests

Live testing shall progress in this order:

1. device discovery and capture only;
2. observe-only board overlays;
3. suggest-only decisions checked by a human;
4. single authorised move with immediate stop;
5. bounded 10-move session;
6. one complete level;
7. multiple level transitions;
8. extended unattended session after acceptance gates pass.

## 16. Acceptance criteria

### 16.1 Recognition acceptance

- **AC-REC-001:** At least 99.5% ordinary-gem identity accuracy on a representative labelled stable-frame corpus.
- **AC-REC-002:** Zero autonomous swipes on corpus frames labelled moving or transitional.
- **AC-REC-003:** Animated sparkle/glow shall not reduce underlying gem identity accuracy below 99% on labelled temporal samples.
- **AC-REC-004:** Any incomplete or ambiguous board shall inhibit autonomous input.

### 16.2 Simulation acceptance

- **AC-SIM-001:** 100% pass rate for all calibrated rule fixtures.
- **AC-SIM-002:** All ordinary swaps, matches, gravity and deterministic cascades shall match observed game outcomes in at least 100 consecutive manually reviewed moves, excluding unknown refill identity.
- **AC-SIM-003:** Every supported special type and pair combination shall have at least one observed regression fixture.

### 16.3 Control acceptance

- **AC-CTL-001:** At least 99 out of 100 commanded swipes shall be accepted correctly in a controlled live test.
- **AC-CTL-002:** No duplicate swipe shall occur during the controlled test.
- **AC-CTL-003:** ADB disconnection, manual stop and missing-board tests shall result in no further input.

### 16.4 Strategic acceptance

- **AC-STR-001:** On a fixed benchmark suite, depth-3 strategic planning shall create more special gems per 100 moves than the immediate-score baseline.
- **AC-STR-002:** The strategic planner shall never return an illegal move.
- **AC-STR-003:** For benchmark boards containing a guaranteed two-move special-gem setup, the planner shall select the setup at the configured reward weights.
- **AC-STR-004:** Planning shall remain within the configured wall-clock budget in at least 99% of benchmark decisions.

### 16.5 Level-transition acceptance

- **AC-LVL-001:** The application shall complete at least 10 consecutive observed level transitions without swiping during a transition.
- **AC-LVL-002:** It shall resume only after a complete stable new board is confirmed.
- **AC-LVL-003:** Plans from the preceding level shall not be reused after reset.

## 17. Agentic implementation plan

The implementation agent shall work in gated increments. It shall not begin live autonomous play before offline and observe-only gates pass.

### Phase 0 — Repository and evidence baseline

1. Create the package structure, configuration schema, tests and developer commands.
2. Record supplied screenshot geometry as an initial profile.
3. Create a decision log listing every unresolved rule from Section 4.
4. Implement fake `FrameSource` and `ActionSink` interfaces first.
5. Add formatting, linting, typing and test commands.

**Gate:** Project installs reproducibly; tests run; no real ADB input can occur by default.

### Phase 1 — ADB observation and geometry

1. Implement device discovery and screenshot capture.
2. Implement resolution/orientation checks.
3. Render the configured 8×8 overlay.
4. Add logical/screen coordinate tests.
5. Implement observe-only CLI.

**Gate:** Overlay aligns with all 64 cells on captured target frames; input remains disabled.

### Phase 2 — Temporal recognition

1. Build labelled crops from screenshots and short recordings.
2. Implement colour and shape/template features.
3. Implement multi-frame median/stability features.
4. Separate gem identity from effects.
5. Produce confidence-calibrated board observations and debug images.
6. Create golden-image regression tests.

**Gate:** Recognition acceptance criteria pass offline.

### Phase 3 — State controller and level transitions

1. Implement the finite-state machine.
2. Implement board motion/stability detection.
3. Implement progress and level recognition.
4. Implement transition observation and new-level confirmation.
5. Test with replay sequences before live observation.

**Gate:** Replay and observe-only sessions never mark a moving/transitioning board as action-ready.

### Phase 4 — Rule engine

1. Implement ordinary swaps, matching, removal and gravity.
2. Add deterministic refill provider.
3. Calibrate one special rule at a time from recordings.
4. Add special combinations only after individual rules pass.
5. Build discrepancy reports comparing prediction to observation.

**Gate:** Simulation acceptance criteria pass for currently declared supported rules. Unsupported effects cause safe pause or conservative handling.

### Phase 5 — Baseline planner

1. Enumerate legal moves.
2. Implement immediate-score heuristic.
3. Implement suggest-only mode.
4. Benchmark legality, determinism and runtime.

**Gate:** Suggested moves are legal and manually validated on at least 50 stable boards.

### Phase 6 — Strategic planner

1. Implement strategic pattern features.
2. Implement beam search and transposition table.
3. Add seeded refill sampling and risk adjustment.
4. Add explainable score decomposition.
5. Compare against immediate-score baseline on fixed boards.

**Gate:** Strategic acceptance criteria pass.

### Phase 7 — Controlled execution

1. Implement swipe conversion and one-outstanding-action enforcement.
2. Add last-moment board equality check.
3. Run one-move tests, then bounded sessions.
4. Implement outcome verification and bounded retry.
5. Collect discrepancies without changing rules live.

**Gate:** Control acceptance criteria pass.

### Phase 8 — Extended play and tuning

1. Run complete levels and validate reset handling.
2. Tune stability timings and heuristic weights from recorded sessions.
3. Add regression tests for every material failure.
4. Run 10-level acceptance session.
5. Produce operator documentation and known-limitations report.

**Gate:** All applicable acceptance criteria pass and unresolved rule limitations are explicit.

## 18. Instructions and constraints for an autonomous coding agent

1. Treat this SRS as the requirements baseline; maintain a requirement-to-test traceability table.
2. Before implementing a game rule, locate evidence or mark it as assumed. Never fabricate rule semantics silently.
3. Prefer small vertical increments that produce executable tests.
4. Keep real input disabled by default and behind an explicit CLI mode.
5. Use recorded frames and fake action sinks for normal development.
6. Do not weaken confidence thresholds merely to make demonstrations proceed.
7. When a captured outcome contradicts the model, preserve the evidence, add a fixture and determine whether recognition, action or rules caused it.
8. Do not introduce ML until the non-ML baseline has measurable failure evidence and a labelled training/evaluation split exists.
9. Do not optimise search before simulator correctness and profiling justify it.
10. Do not couple planner code to pixel coordinates or OpenCV types.
11. Do not couple vision code to ADB subprocess calls.
12. Never run destructive or account-changing phone commands.
13. At the end of each phase, report implemented requirements, tests, observed limitations and the next gate.
14. Stop and request clarification if an unknown rule would materially affect safe input or simulation correctness.

## 19. Deliverables

The completed implementation shall include:

- source code and dependency definition;
- typed configuration schema;
- target-device recognition profile;
- versioned game rule set;
- CLI commands described in Section 10;
- unit, property, golden-image and replay tests;
- representative test fixtures with provenance;
- requirement-to-test traceability matrix;
- operator guide for pairing wireless ADB and starting each mode;
- calibration guide for new recordings/effects;
- architecture and rule-model documentation;
- benchmark report comparing strategic and immediate-score planners;
- known limitations and unresolved-rule report;
- sample redacted session output.

## 20. Definition of done

The project is complete for version 1 when:

1. all mandatory functional requirements are implemented or explicitly waived;
2. all applicable acceptance criteria pass;
3. the system completes at least 10 consecutive level transitions without unsafe input;
4. the strategic planner measurably outperforms the immediate-score baseline in special-gem creation on the fixed benchmark;
5. recorded sessions reproduce recognition and decisions using saved configuration and seed;
6. the application stops safely on uncertainty, disconnection, unexpected UI or manual interruption;
7. documentation enables another engineer or implementation agent to install, calibrate, test and operate the system without undocumented steps.

## Appendix A — Initial calibration record

The supplied screenshots show the same level at different scores and board states. One white/silver gem has a visible animated glow. This establishes that temporal effect handling is required, but does not establish the semantic meaning of the glow. The implementation shall therefore preserve `WHITE` as the tentative identity while labelling the overlay separately until a recording confirms the effect.

## Appendix B — Recommended first additional evidence

Collect a short lossless or high-quality screen recording containing:

1. at least 10 seconds of an untouched stable board to observe idle animations;
2. an ordinary three-gem swap and cascade;
3. every known special-gem creation pattern;
4. activation of every special gem;
5. every available special-special combination;
6. a hint or selection animation;
7. progress bar reaching full;
8. the entire level transition and board reset;
9. the first stable board of the next level.

Frame timestamps and the user's actual swipes should be noted when possible. This evidence is sufficient to replace most Section 4 assumptions with executable rule fixtures.
