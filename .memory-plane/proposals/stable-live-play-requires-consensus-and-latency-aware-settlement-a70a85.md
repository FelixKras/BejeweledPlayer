---
id: mp-20260813-b5eea70a85
kind: procedure
title: Stable live play requires consensus and latency-aware settlement
scope: project
status: proposed
created_at: 2026-08-13T22:58:51.882244Z
author: Forge
confidence: 0.97
source_refs:
  - src/bejeweled_player/turn.py; tests/test_settlement.py; sessions/play-20260813T224848.773577Z/summary.json; uv run pytest -q (80 passed)
tags:
  - live-play-stability
---

# Stable live play requires consensus and latency-aware settlement

For the Pixel 9 Pro wireless-ADB profile, require two consecutive identical recognized boards selecting the same move before swiping. During settlement, allow up to two UNKNOWN cells and up to eight ordinary classification differences for simultaneous flame/hint animation, but retain the requirement to observe at least two changed ordinary cells relative to the pre-swipe board. Use a 120-second settlement timeout when wireless screenshots take 25-40 seconds. Keep the device awake, unlocked, in Zen mode, and Bejeweled foreground. Strict zero-UNKNOWN recognition remains required before every swipe.
