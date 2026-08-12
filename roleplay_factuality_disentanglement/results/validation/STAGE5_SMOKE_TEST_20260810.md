# Stage 5 smoke-test verification

Run: `pilot_v1_smoke_8_20260810T021351Z`

- Dataset version: `pilot_v1`
- Model: `google/gemma-3-1b-it`
- Resolved revision: `dcc83ea841ab6100d6b47a070329e1ba4cf78752`
- Examples: 8, with 2 in each frame-by-factuality condition
- Activation shape: `[8, 26, 1152]`
- Saved dtype: `float32`
- All values finite: yes
- Saved rows exactly equal their eight individual cache entries: yes
- Extraction position: final token of the forced answer
- Runtime concern: PyTorch reported `2.10.0+cpu`; the smoke test did not use CUDA

The smoke-test implementation gate passed. Do not begin the full run until CPU versus CUDA execution
is chosen deliberately.
