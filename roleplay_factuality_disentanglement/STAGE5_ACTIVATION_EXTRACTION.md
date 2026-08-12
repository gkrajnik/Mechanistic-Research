# Stage 5: activation extraction

The extractor uses the frozen `pilot_v1` dataset and the model configured once in `config.yaml`.
It measures the output of every transformer block at the final token of the forced `Yes` or `No`
answer, matching the earlier factuality-direction convention.

## Safe first run

From the `roleplay_factuality_disentanglement` folder, first validate selection without loading a
model:

```powershell
python scripts\02_extract_activations.py --dry-run
```

Then run the eight-example GPU smoke test:

```powershell
python scripts\02_extract_activations.py
```

After changing the PyTorch/CUDA installation, use `--ignore-cache` once so the GPU is tested with
fresh model passes rather than merely reading the earlier CPU-created cache:

```powershell
python scripts\02_extract_activations.py --ignore-cache
```

Only after the smoke-test manifest and activation shape are checked, run all 480 examples:

```powershell
python scripts\02_extract_activations.py --full
```

The full run stops if the model loads on CPU. This protects against accidentally beginning a very
long extraction with a CPU-only PyTorch installation. If CPU execution is deliberate, the safeguard
can be overridden with `--full --allow-cpu-full`.

The first smoke test passed data, shape, finite-value, and cache-integrity checks, but its manifest
reported `torch_version: 2.10.0+cpu`. Configure a CUDA-enabled PyTorch environment before the full
run if GPU execution is intended.

The replacement GPU smoke test `pilot_v1_smoke_8_20260810T023254Z` passed on `cuda:0` with PyTorch
`2.10.0+cu128`. The full extraction is cleared to run.

The full run `pilot_v1_full_20260810T023517Z` produced `[480, 26, 1152]` finite activations with
complete metadata and cache agreement. A short independent same-GPU repeatability run is the final
Gate 5 check before probe training.

The repeat run `pilot_v1_smoke_4_20260810T031423Z` exactly matched the corresponding full-run
activations for one example from every condition. Gate 5 is passed.

Runs are timestamped under `results/activations/`; individual examples are cached under
`results/activation_cache/`, so an interrupted extraction can resume without repeating completed
model passes. Never edit the frozen dataset to change the model—change only `model.name` in
`config.yaml`.
