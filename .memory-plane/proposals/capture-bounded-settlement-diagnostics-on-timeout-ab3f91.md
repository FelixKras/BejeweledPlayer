---
id: mp-20260818-129eab3f91
kind: procedure
title: Capture bounded settlement diagnostics on timeout
scope: project
status: proposed
created_at: 2026-08-18T04:32:11.259092Z
author: Forge
confidence: 0.95
source_refs:
  - src/bejeweled_player/turn.py; tests/test_settlement.py; pytest; ruff; mypy
tags:
  - settlement-debugging
---

# Capture bounded settlement diagnostics on timeout

When post-swipe settlement times out, retain the last five captured frames in the turn session under settlement-debug/ and write summary.json with frame IDs, progress fraction, recognition errors, recognized boards, board-change status, foreground-anchor change fraction, and anchor stability. This supplements existing error retention, which only saved the before frame, while bounding disk usage.
