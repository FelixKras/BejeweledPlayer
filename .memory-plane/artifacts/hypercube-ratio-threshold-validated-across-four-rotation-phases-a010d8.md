---
id: mp-20260813-c0c3a010d8
kind: decision
title: Hypercube ratio threshold validated across four rotation phases
scope: project
status: approved
created_at: 2026-08-13T09:23:43.932500Z
author: Forge
confidence: 0.95
approved_at: 2026-08-13T09:41:41.132741Z
reviewer: Felix
source_refs:
  - datasets/vision-20/hypercube-phases.jpg; datasets/vision-20/special-gems-level3.jpg; src/bejeweled_player/board.py; tests/test_turn.py; pytest
tags:
  - hypercube
---

# Hypercube ratio threshold validated across four rotation phases

A second real fixture contains four hypercubes spanning warm-, blue-, purple-, and green-dominant rotation phases. Their central-body second/first broad hue-family ratios are 0.995, 0.557, 0.829, and 0.533. Hypercube detection therefore uses ratio >=0.50 without a dominant-family restriction. Golden replay detects all five confirmed hypercubes across two fixtures and no hypercubes on Level 9/14 regressions.
