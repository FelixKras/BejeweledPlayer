---
id: mp-20260814-9bae516c66
kind: procedure
title: Completion screens use guarded Continue detection
scope: project
status: proposed
created_at: 2026-08-14T04:24:56.702535Z
author: Forge
confidence: 0.9
source_refs:
  - src/bejeweled_player/turn.py; src/bejeweled_player/adb/input.py; tests/test_turn.py; tests/test_adb_input.py; user-provided Rank Up screenshot; pytest (83 passed)
tags:
  - completion-ui
---

# Completion screens use guarded Continue detection

Recognize Rank/Badge and Level completion screens by requiring both a large orange result panel in the lower screen and a wide green pill-shaped contour below 55% screen height. In execute-authorized turn loops only, tap the detected contour center, wait, and resume capture; dry-run mode never taps. This avoids OCR dependence and prevents ordinary green gems from triggering Continue.
