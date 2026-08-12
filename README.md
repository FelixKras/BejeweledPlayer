# BejeweledPlayer

PC-side Python implementation of the **Wireless-ADB Strategic Match-3 Autoplayer** SRS v1.0. The current MVP is a read-only Phase 1 observation slice and cannot send live input through its CLI.

## Development setup

Requirements: Python 3.12 or newer. On Debian/Ubuntu, install venv support first if necessary:

```bash
sudo apt install python3.12-venv
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

Run the Phase 0 checks:

```bash
pytest
ruff check .
mypy
autoplayer validate-config --config config/target_720x1536.toml
```

List connected devices:

```bash
autoplayer devices
```

Set `device.serial` in `config/target_720x1536.toml`, then capture one lossless frame and render the calibrated grid:

```bash
autoplayer observe --config config/target_720x1536.toml
```

For the calibrated Pixel 9 Pro at `960x2142`:

```bash
autoplayer observe --config config/pixel9pro_960x2142.toml
```

Render the overlay against an existing screenshot without ADB:

```bash
autoplayer render-debug \
  --config config/target_720x1536.toml \
  --frame board.png \
  --output board.overlay.png
```

Perform a dry run of one adjacent logical swipe:

```bash
autoplayer swipe \
  --config config/pixel9pro_960x2142.toml \
  --source 1 4 \
  --destination 2 4
```

Add `--execute` to authorize exactly that one swipe. The command validates adjacency and board bounds, sends one ADB input command, and exits. It does not yet recognize board stability or verify that the current board matches a planning frame, so an operator must recapture and inspect immediately before execution.

`calibrate`, `suggest`, `play`, `replay`, and `simulate` remain gated.

## Minimal Playing Turn

Capture the foreground board and print one deterministic immediate-match decision:

```bash
autoplayer turn --config config/pixel9pro_960x2142.toml
```

Authorize that one selected move, capture the settled outcome, and exit:

```bash
autoplayer turn --config config/pixel9pro_960x2142.toml --execute
```

The minimal turn recognises the seven ordinary colors, rejects low-color or insufficiently diverse screens, rejects boards containing unresolved matches, evaluates every adjacent swap, and chooses the first highest-scoring immediate match deterministically. It does not model special gems, cascades, future turns, or continuous play.

Run a bounded, recorded sequence using the same capture/validation gate before every move:

```bash
autoplayer multi-turn \
  --config config/pixel9pro_960x2142.toml \
  --turns 25 \
  --execute
```

Each multi-turn session contains an incrementally updated `summary.json` plus raw and annotated before/after frames for every completed turn. Execution stops on the first unsafe or unrecognised state.

For unbounded play, stop with `Ctrl+C`:

```bash
autoplayer play \
  --config config/pixel9pro_960x2142.toml \
  --execute
```

Each turn re-captures the board, prioritizes 5/4 matches, then ranks 3-matches by setup potential and mobility. It polls after the swipe with a 50 ms minimum wait and 80 ms cadence until a valid settled board is observed. Settlement allows exact equality, special-cell-only flicker, or one ordinary-cell flicker, with a default 25 second timeout. Full-screen transitions, special-gem ambiguity, unrelated screens, and persistent motion stop the run safely. `summary.json` is updated after every completed turn.

## Baseline status

- Initial target profile: 720x1536 portrait, 8x8 board, approximate bounds `(0, 320)` to `(720, 1005)`.
- Input: disabled.
- Recognition profile: untrained.
- Rule set: unresolved assumptions; not safe for simulation or play.
- Hardware-free development: `FakeFrameSource` and `FakeActionSink` are available.

See `docs/TRACEABILITY.md` and `docs/UNRESOLVED_RULES.md` before implementing later phases.
