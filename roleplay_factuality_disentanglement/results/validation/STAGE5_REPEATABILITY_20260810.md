# Stage 5 repeatability verification

Repeat run: `pilot_v1_smoke_4_20260810T031423Z`

- Runtime device: `cuda:0`
- PyTorch: `2.10.0+cu128`
- Shape: `[4, 26, 1152]`
- Coverage: one example from each frame-by-factuality condition
- All values finite
- Comparison target: `pilot_v1_full_20260810T023517Z`
- Maximum absolute difference for every repeated example: `0.0`
- Mean absolute difference for every repeated example: `0.0`
- Exact array equality: 4 of 4 examples

Gate 5 passed: repeated extraction produced identical shapes and exactly reproducible activations.
