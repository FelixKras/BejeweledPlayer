---
id: mp-20260818-0f480ea4c5
kind: decision
title: Commit active special-gem recognition and strategy changes
scope: project
status: proposed
created_at: 2026-08-18T03:47:12.520220Z
author: Forge
confidence: 0.9
source_refs:
  - src/bejeweled_player/board.py; tests/test_strategy.py; tests/test_turn.py; datasets/generate_gem_infographic.py; datasets/vision-20/gem-histogram-infographic.png; pytest; ruff; mypy
tags:
  - special-gems
---

# Commit active special-gem recognition and strategy changes

The remaining board recognizer, strategy, regression-test, infographic generator, generated infographic, and memory-plane migration files are active project artifacts and pass pytest (89), ruff, mypy, and infographic regeneration. They should be preserved in version control; runtime play logs remain excluded.
