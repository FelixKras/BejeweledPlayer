---
id: mp-20260813-55c350df14
kind: decision
title: Classify ordinary gems by hue-template correlation
scope: project
status: proposed
created_at: 2026-08-13T04:14:53.592835Z
author: Forge
confidence: 0.92
source_refs:
  - src/bejeweled_player/board.py; src/bejeweled_player/turn.py; tests/test_turn.py; pytest; sessions/play-20260812T203742.274360Z
tags:
  - recognition
---

# Classify ordinary gems by hue-template correlation

Ordinary saturated gems are classified by normalized 18-bin HSV hue histograms correlated against six color-family templates. Classification requires correlation >=0.35, runner-up margin >=0.08, and >=0.55 mass in the winning family; otherwise label UNKNOWN and reject the board before planning. White and special detection remain separate. Calibration over 500 historical frames rejected 8 ambiguous cells, while the known Level 9 regression still selects the four-match.
