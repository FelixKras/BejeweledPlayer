# Vision-20 provisional labels

This dataset contains 20 saved 8x8 boards (1,280 cell crops) from the Pixel 9 Pro
profile. Boards 1-3 are known recognition failures; boards 4-20 sample the long
run, including repeated states and animated glow/hint effects.

`labels.json` records one-based row/column coordinates and source provenance.
Labels were seeded by the current classifier and reviewed against the board
contact sheets. They are provisional vision labels, not independent human ground
truth. Any future classifier evaluation must not train and score on the same
labels without manual review.

Supported labels are `red`, `green`, `blue`, `yellow`, `purple`, `orange`,
`white`, `hypercube`, `shining_special`, and `uncertain`. No visually
distinct special gem was present in this selection. Fire, glow, and hint effects
were treated separately from the underlying ordinary gem identity.

Regenerate crops and sheets with:

```bash
.venv/bin/python3 datasets/build_vision_set.py
```
