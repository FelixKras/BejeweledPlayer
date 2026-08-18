---
id: mp-20260813-cd64be6aeb
kind: procedure
title: Launch unbounded play against a dynamic ADB endpoint
scope: project
status: proposed
created_at: 2026-08-13T17:46:42.509643Z
author: Forge
confidence: 0.98
source_refs:
  - README.md lines 92-100; config/pixel9pro_960x2142.toml; successful operational run
tags:
  - unbounded-play
---

# Launch unbounded play against a dynamic ADB endpoint

For a dynamic wireless-ADB endpoint, connect with adb connect, copy the matching device profile to a temporary config outside the repository, replace only device.serial with the current endpoint, and launch autoplayer play --config <temporary-config> --execute under nohup with output redirected to a temporary log. Verify the detached PID remains alive after startup. Do not persist the endpoint, PID, temporary config, or log location in project memory.
