---
id: mp-20260813-138febe1e0
kind: decision
title: Detect hypercube by warm-secondary hue-family ratio
scope: project
status: proposed
created_at: 2026-08-13T06:56:43.922258Z
author: Forge
confidence: 0.85
source_refs:
  - src/bejeweled_player/board.py; tests/test_turn.py; datasets/vision-20/special-gems-level3.jpg; datasets/vision-20/labels.json; pytest
tags:
  - hypercube
---

# Detect hypercube by warm-secondary hue-family ratio

Hypercube detection now requires the central gem-body histogram's dominant broad hue family to be warm (family 0) and the second-largest family to be at least 25% of the largest. The confirmed Level 3 hypercube has ratio 0.502; 551 labeled red/orange/yellow cubes remain below 0.07 centrally. Warm dominance prevents the Level 14 faceted-purple false positive. This threshold is calibrated from only one confirmed hypercube and requires more real rotation-phase examples.
