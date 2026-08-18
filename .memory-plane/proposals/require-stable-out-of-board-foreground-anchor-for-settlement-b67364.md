---
id: mp-20260818-f1eab67364
kind: decision
title: Require stable out-of-board foreground anchor for settlement
scope: project
status: proposed
created_at: 2026-08-18T03:22:43.467376Z
author: Forge
confidence: 0.9
source_refs:
  - src/bejeweled_player/turn.py; src/bejeweled_player/config.py; config/pixel9pro_960x2142.toml; config/target_720x1536.toml; tests/test_settlement.py; pytest; ruff; mypy
tags:
  - settlement-safety
---

# Require stable out-of-board foreground anchor for settlement

Settlement now compares a configured non-animated foreground ROI outside the board between consecutive valid captures and only accepts localized board changes when that anchor is stable. Pixel 9 Pro uses the settings-button area (0,1500)-(330,1720); the 720x1536 profile uses (0,1070)-(250,1230), with an 8% changed-pixel threshold. The prior latency-based acceptance shortcut was removed because screenshot capture duration is not evidence that the game settled. Regression coverage verifies board-only changes do not affect the anchor and broad anchor changes reject stability.
