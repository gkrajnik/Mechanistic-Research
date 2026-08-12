# Stage 5 full-extraction verification

Run: `pilot_v1_full_20260810T023517Z`

- Dataset: `pilot_v1`
- Model: `google/gemma-3-1b-it`
- Model revision: `dcc83ea841ab6100d6b47a070329e1ba4cf78752`
- Runtime device: `cuda:0`
- PyTorch: `2.10.0+cu128`
- Examples: 480
- Activation shape: `[480, 26, 1152]`
- Saved dtype: `float32`
- Combined activation file size: 26.27 MiB
- Conditions: 120 rows each for normal/factual, normal/nonfactual, roleplay/factual, and
  roleplay/nonfactual
- Topic splits: 288 train, 96 validation, 96 test
- Cache use: 8 previously verified GPU rows reused; 472 rows computed in this run
- All values finite
- All 480 combined rows exactly match their individual cache entries
- No cache shape errors

The full extraction passed integrity, shape, balance, and metadata checks. A short independent
same-GPU repeatability run remains before declaring Gate 5 fully passed.
