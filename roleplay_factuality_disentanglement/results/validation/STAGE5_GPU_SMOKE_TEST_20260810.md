# Stage 5 GPU smoke-test verification

Run: `pilot_v1_smoke_8_20260810T023254Z`

- Dataset: `pilot_v1`
- Model: `google/gemma-3-1b-it`
- Model revision: `dcc83ea841ab6100d6b47a070329e1ba4cf78752`
- Runtime device: `cuda:0`
- PyTorch: `2.10.0+cu128`
- Activation shape: `[8, 26, 1152]`
- Coverage: two examples in each frame-by-factuality condition
- All eight activations freshly computed by the model (`--ignore-cache`)
- All activation values finite
- All eight combined rows exactly match their individual cache files

The GPU smoke test passed. The full 480-example extraction is cleared to run without
`--ignore-cache`; the eight verified cache entries may be reused.
