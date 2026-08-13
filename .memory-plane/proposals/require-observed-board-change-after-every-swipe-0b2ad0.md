---
id: mp-20260813-c24d0b2ad0
kind: decision
title: Require observed board change after every swipe
scope: project
status: proposed
created_at: 2026-08-13T03:32:27.023659Z
author: Forge
confidence: 0.99
source_refs:
  - src/bejeweled_player/turn.py; tests/test_settlement.py; sessions/play-20260812T203742.274360Z/summary.json; pytest
tags:
  - settlement-safety
---

# Require observed board change after every swipe

Post-swipe settlement must observe at least two changed ordinary cells relative to the pre-swipe recognized board before accepting stable frames. This prevents rejected/no-op swaps caused by recognition errors from being recorded as successful and retried indefinitely. The 2026-08-12 run showed 2,976 repeats of one swap and 3,637 consecutive repeated/reversed pairs before this guard.
