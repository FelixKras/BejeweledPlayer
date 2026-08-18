---
id: mp-20260818-5d2282012f
kind: claim
title: Special ordinary swaps were misclassified as unchanged
scope: project
status: proposed
created_at: 2026-08-18T22:12:25.842796Z
author: Forge
confidence: 0.99
source_refs:
  - sessions/play-20260818T193431.759379Z/turn-20260818T195354.272157Z/summary.json; sessions/play-20260818T193431.759379Z/turn-20260818T195354.272157Z/00-e32aa2fbf4614704804274991fa92845.png; src/bejeweled_player/turn.py; tests/test_settlement.py; pytest
tags:
  - settlement-safety
---

# Special ordinary swaps were misclassified as unchanged

The 192.168.41.98:36167 run stopped after a successful-looking swap because the post-swipe guard counted only ordinary-label-to-ordinary-label changes. The debug summary and frames showed a special/ordinary swap with stable foreground anchor and unchanged recognized values across subsequent frames; both changed cells were excluded because one side was a Flame Gem label. Settlement change detection now compares underlying gem_color identities, so special/ordinary swaps count while pure special-effect label flicker does not. Regression coverage was added.
