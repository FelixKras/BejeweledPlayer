---
id: mp-20260818-52851d50bb
kind: decision
title: Expand hypercube recognition and retry confirmed no-op swaps
scope: project
status: proposed
created_at: 2026-08-18T22:33:20.673501Z
author: Forge
confidence: 0.95
supersedes: mp-20260813-c0c3a010d8
source_refs:
  - sessions/play-20260818T221624.695950Z/turn-20260818T222015.676825Z; datasets/vision-20/hypercube-dark-red-phase.png; src/bejeweled_player/board.py; src/bejeweled_player/turn.py; tests/test_turn.py; tests/test_settlement.py; tests/test_strategy.py; pytest
tags:
  - hypercube
---

# Expand hypercube recognition and retry confirmed no-op swaps

A Level 124 dark/red hypercube phase had a second-family ratio of 0.406 and was misclassified as red, outside the four previously validated phases. Hypercube recognition now also accepts ratio >=0.35 when saturated coverage is below 70% and at least three hue bins are significant; the saved phase replays as hypercube while the full regression set remains clean. When three consecutive valid captures have a stable foreground anchor and differ from the pre-swipe board in at most one gem, settlement classifies the swipe as a confirmed no-op. Unbounded play blacklists that coordinate pair and tries up to two alternate moves before stopping.
