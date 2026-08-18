---
id: mp-20260813-68fccb2562
kind: decision
title: Unknown gems use a conservative color-evidence ensemble
scope: project
status: proposed
created_at: 2026-08-13T19:25:42.306776Z
author: Forge
confidence: 0.95
source_refs:
  - src/bejeweled_player/board.py; tests/test_turn.py; uv run pytest -q (78 passed); uv run ruff check .; uv run mypy
tags:
  - gem-recognition
---

# Unknown gems use a conservative color-evidence ensemble

When primary hue-template recognition returns UNKNOWN, classify_unknown_gem combines saturation-weighted hue-family evidence over full, middle, and central elliptical regions plus a global pixel vote and separate neutral-bright white score. Accept only a candidate scoring at least 0.42 with a 0.12 lead; otherwise preserve UNKNOWN. The fallback is unknown-only and keeps primary recognition and hypercube/special detection unchanged.
