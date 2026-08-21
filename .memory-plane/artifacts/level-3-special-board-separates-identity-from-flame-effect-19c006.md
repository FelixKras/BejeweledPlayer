---
id: mp-20260813-3f1019c006
kind: claim
title: Level 3 special board separates identity from flame effect
scope: project
status: approved
created_at: 2026-08-13T06:09:23.182270Z
author: Forge
confidence: 0.99
approved_at: 2026-08-13T09:41:41.161083Z
reviewer: Team
source_refs:
  - datasets/vision-20/special-gems-level3.jpg; datasets/vision-20/special-gems-level3.json; tests/test_turn.py
tags:
  - special-recognition
---

# Level 3 special board separates identity from flame effect

Telegram message 23705 provides a labeled 8x8 Level 3 fixture with flame effects at r2c6 red, r4c1 white, and r8c4 red, plus a multicolor cube at r6c7. The current recognizer preserves all flaming gems' underlying ordinary identity and safely returns UNKNOWN for the cube. Exact image, geometry, labels, and regression test are stored in datasets/vision-20.
