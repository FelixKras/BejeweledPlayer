---
id: mp-20260812-597d49cc05
kind: decision
title: Immediate match size is primary move rank
scope: project
status: approved
created_at: 2026-08-12T19:38:53.972548Z
author: Forge
confidence: 0.98
approved_at: 2026-08-13T09:41:41.045425Z
reviewer: Felix
source_refs:
  - src/bejeweled_player/board.py; tests/test_strategy.py; pytest tests/test_strategy.py tests/test_board.py
tags:
  - move-ranking
---

# Immediate match size is primary move rank

find_best_move ranks candidates lexicographically by immediate matched-cell count before strategic setup and mobility, guaranteeing that a 4-match is preferred over every 3-match and a 5-match over smaller matches.
