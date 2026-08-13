---
id: mp-20260813-a7bcb8ff26
kind: claim
title: Two hue families do not identify rotating gems
scope: project
status: proposed
created_at: 2026-08-13T04:34:42.997933Z
author: Forge
confidence: 0.98
source_refs:
  - src/bejeweled_player/board.py; tests/test_turn.py; sessions/play-20260813T042854.732756Z/turn-20260813T042859.083981Z/before.png; pytest
tags:
  - special-recognition
---

# Two hue families do not identify rotating gems

The rejected live swap was caused by ordinary faceted purple gems spanning blue and purple hue families and being labeled as rotating specials. Rotating-special detection now requires three significant hue families. Replaying the failed Level 14 frame changes four false specials to purple and yields a legal ordinary 3-match.
