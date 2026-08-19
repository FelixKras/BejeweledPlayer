---
id: mp-20260819-4ae06faa67
kind: decision
title: Require saturated body evidence for hypercube recognition
scope: project
status: proposed
created_at: 2026-08-19T02:51:18.554975Z
author: Forge
confidence: 0.98
supersedes: mp-20260818-52851d50bb
source_refs:
  - sessions/play-20260818T223721.482671Z/summary.json; sessions/play-20260818T223721.482671Z/turn-20260819T021123.548602Z; datasets/vision-20/white-gem-dark-overlay.png; datasets/vision-20/hypercube-dark-red-phase.png; src/bejeweled_player/board.py; tests/test_turn.py; pytest
tags:
  - hypercube
---

# Require saturated body evidence for hypercube recognition

The first retry-enabled live run completed 1,676 moves before a dark-overlay white gem was falsely classified as a hypercube. Its saturated-pixel fraction was 0.064 versus 0.58 for the confirmed dark/red hypercube phase. Hypercube recognition now requires at least 25% saturated body pixels in addition to the multi-hue criteria. Golden regressions include both the confirmed dark/red hypercube and the dark-overlay white negative. Replaying the failed planning frame now selects an ordinary scoring move instead of a false hypercube activation.
