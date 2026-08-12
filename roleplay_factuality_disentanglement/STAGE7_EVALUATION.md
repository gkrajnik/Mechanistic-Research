# Stage 7: locked disentanglement evaluation

This stage evaluates the frozen layer-22 probes without changing their weights, thresholds, or
layer. It reports held-out-topic, held-out-wording, and joint-generalization performance, subgroup
metrics, pair-level bootstrap confidence intervals, direction cosine similarity across layers, and
training-only two-margin control analyses.

Run:

```powershell
python scripts\04_evaluate_probes.py
```

Outputs are timestamped under `results/evaluation/`. Test data is used only for final scoring, never
for fitting, threshold selection, or layer selection.

The first locked evaluation did not pass Gate 7. Both probes scored 0.50 balanced accuracy when
topic and wording were jointly held out. The result is preserved as evidence that the current pilot
directions do not generalize robustly enough for the planned conversation-level interpretation.
