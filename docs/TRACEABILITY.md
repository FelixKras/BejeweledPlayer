# Requirement Traceability

Status values: `Implemented`, `Partial`, `Planned`, or `Blocked by evidence`.

| Requirement | Status | Implementation | Test/evidence |
|---|---|---|---|
| FR-CFG-001 | Implemented | `config.load_config` (TOML) | `test_initial_profile_loads` |
| FR-CFG-002 | Partial | Initial Phase 0 profile fields | Profile validation tests; remaining sections planned |
| FR-CFG-003 | Planned | Phase 1 CLI/run metadata | None |
| FR-CFG-004 | Partial | Strict known-key and value validation | `test_unknown_root_key_is_rejected` |
| FR-CFG-005 | Implemented | `planner.random_seed` | Profile load test |
| FR-ADB-001 | Implemented | `adb.list_devices`, `autoplayer devices` | `test_device_listing_parses_state_and_details` |
| FR-ADB-002 | Implemented | Configured device serial | Configuration and transport tests |
| FR-ADB-003 | Implemented | `exec-out screencap -p`, preserved PNG bytes | `test_capture_returns_validated_lossless_frame` |
| FR-ADB-004 | Implemented | Configurable timeout and bounded retries | Transport tests and Pixel 9 Pro live captures |
| FR-ADB-005 | Implemented | Configurable adjacent-cell swipe | `test_action_sink_builds_one_calibrated_swipe_command`; live action `76d062b16d7c4857a10a9fa6de1a7aee` |
| FR-ADB-006 | Implemented | Endpoints derive only from validated board coordinates | Move/geometry and action-sink tests |
| FR-ADB-007 | Implemented | One-turn command sends at most one action before outcome capture | Action-sink and live single-swipe evidence |
| FR-GEO-001 | Implemented | `BoardGeometry` | `test_geometry_maps_first_and_last_cells` |
| FR-GEO-002 | Implemented | `Coordinate` | Geometry tests |
| FR-GEO-003 | Implemented | `BoardGeometry.center` | Geometry tests |
| FR-VIS-001 | Implemented | UUID and monotonic timestamp on `Frame` | Capture test |
| FR-VIS-002 | Implemented | Exact configured dimension/orientation check | `test_capture_rejects_wrong_resolution` |
| FR-REC-010 | Partial | 8x8 coordinate overlay | `test_overlay_renders_configured_grid`; labels/confidence planned |
| FR-REC-009 | Partial | Low-color, low-diversity, or unresolved-match boards inhibit turn input | `test_turn_rejects_unrelated_low_color_screen`; confidence model planned |
| FR-SIM-002 | Implemented | Right/down adjacent swap enumeration | Board move tests |
| FR-SIM-003 | Partial | Ordinary swaps without a new match are rejected | Immediate move tests; special effects unsupported |
| FR-SIM-004 | Implemented | Horizontal/vertical union of matched cells | `test_matched_cells_detects_horizontal_and_vertical_runs` |
| FR-PLN-001 | Implemented | Every adjacent ordinary swap is evaluated | Immediate decision tests |
| FR-PLN-004 | Implemented | Minimal turn can execute only the selected first move | CLI/action-sink design |
| FR-PLN-012 | Implemented | Fixed traversal order provides deterministic ties | Immediate decision tests |
| FR-PLN-004 | Implemented | `play` executes only one newly observed move per cycle | `run_unbounded` |
| FR-PLN-007 | Implemented | Configurable wall-clock settlement timeout | `run_unbounded`/CLI validation |
| FR-EVL-001 | Partial | 5/4 match priority plus setup/mobility tie-breaks | Strategy tests |
| FR-STB-001 | Partial | Two consecutive equal valid symbolic boards | `_capture_settled`; temporal frame corpus planned |
| FR-STB-005 | Implemented | Configurable minimum quiet wait after swipe | `--settle-minimum-seconds` |
| FR-LVL-001 | Partial | Near-full progress bar enters transition wait; multi-signal level identity planned | `progress_fraction`, settlement loop |
| FR-LVL-003 | Implemented | No swipe while progress is near full or transition is active | `_capture_settled` |
| FR-LVL-004 | Implemented | Observe-only polling during transition | `_capture_settled` |
| FR-LVL-005 | Partial | Bar reset plus stable board; level OCR planned | Transition regression evidence |
| FR-ACT-001 | Implemented | Validated domain `Move` | `test_move_must_be_adjacent` |
| FR-ACT-002 | Implemented | `BoardGeometry.center` | Geometry tests |
| FR-ACT-003 | Partial | Configurable swipe duration; endpoint inset planned | Action-sink command test |
| FR-ACT-004 | Planned | No automatic last-moment board equality check | Operator recapture required |
| FR-ACT-006 | Partial | Unique action receipt emitted; structured linkage planned | Live action receipt and before/after frames |
| FR-ACT-007 | Implemented | CLI sends at most one command and exits | Action-sink command test; live single-swipe test |
| NFR-SEC-001 | Implemented | ADB subprocess argument arrays, no shell | Transport unit tests |
| NFR-MNT-001 | Partial | Domain/interfaces separated; experimental modules quarantined | Architecture review |
| NFR-TST-001 | Partial | Fake frame source/action sink | `test_fake_sink_records_without_hardware` |

All requirements not listed above remain `Planned` or, for unknown game mechanics, `Blocked by evidence`. The table will expand by phase rather than claiming blanket compliance.
