---
id: mp-20260815-a694739cfb
kind: decision
title: Special-aware utility supersedes immediate-match-first ranking
scope: project
status: proposed
created_at: 2026-08-15T17:23:17.797898Z
author: Forge
confidence: 0.95
supersedes: mp-20260812-597d49cc05
source_refs:
  - src/bejeweled_player/board.py; tests/test_strategy.py; tests/test_turn.py; pytest: 87 passed
tags:
  - strategy
---

# Special-aware utility supersedes immediate-match-first ranking

The planner now represents color-bearing Flame Gems as labels 10-16 and Star Gems as 17-23, with hypercube remaining 7. Colored specials participate in ordinary matches. All ordinary and hypercube swaps are ranked in one utility path; straight five creation receives a dominant bonus and direct Flame/Star blast exposure of stored hypercubes receives a dominant penalty. This intentionally supersedes lexicographic immediate-match-first ranking.
