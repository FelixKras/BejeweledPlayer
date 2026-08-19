---
id: mp-20260819-949aa91e75
kind: procedure
title: Run exhaustive labeled recognition regressions
scope: project
status: proposed
created_at: 2026-08-19T04:35:46.630684Z
author: Forge
confidence: 0.99
source_refs:
  - tests/test_recognition.py; datasets/vision-20/labels.json; datasets/vision-20/special-gems-level3.json; pytest tests/test_recognition.py; pytest
tags:
  - recognition-regression
---

# Run exhaustive labeled recognition regressions

Real-image recognition regressions live in tests/test_recognition.py. The suite parameterizes all 1,280 records from datasets/vision-20/labels.json and compares gem_color(recognized_label) with the labeled underlying identity, preserving valid Flame-effect labels. It also derives the complete special-board expectation from special-gems-level3.json and checks known hypercube phases plus the dark-overlay negative. Run pytest tests/test_recognition.py for recognition-only verification; the current suite contains 1,284 cases.
