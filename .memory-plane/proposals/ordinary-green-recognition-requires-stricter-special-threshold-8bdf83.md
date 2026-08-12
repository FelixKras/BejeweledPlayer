---
id: mp-20260812-a9be8bdf83
kind: claim
title: Ordinary green recognition requires stricter special threshold
scope: project
status: proposed
created_at: 2026-08-12T19:47:54.899493Z
author: Forge
confidence: 0.95
source_refs:
  - src/bejeweled_player/board.py; tests/test_turn.py; sessions/play-20260812T194706.235368Z/summary.json
tags:
  - recognition
---

# Ordinary green recognition requires stricter special threshold

The prior green-special heuristic misclassified many normal rendered green gems as special value 8, causing false no-move exits. Green specials now require histogram saturation below 170 and value below 190; a live run subsequently completed a score-4 turn.
