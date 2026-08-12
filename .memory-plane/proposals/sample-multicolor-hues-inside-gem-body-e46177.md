---
id: mp-20260812-226ce46177
kind: decision
title: Sample multicolor hues inside gem body
scope: project
status: proposed
created_at: 2026-08-12T20:05:08.177733Z
author: Forge
confidence: 0.98
source_refs:
  - src/bejeweled_player/board.py; tests/test_turn.py; sessions/turn-20260812T194929.451558Z/before.png; pytest
tags:
  - recognition
---

# Sample multicolor hues inside gem body

Multicolor detection uses a histogram radius of one quarter cell size rather than one third. The smaller central region excludes board artwork and animated edge glows while retaining separated hues inside true multicolor gems. On the Level 9 regression frame this changes false special labels back to ordinary colors and selects the four-match swap (6,2)-(6,3).
