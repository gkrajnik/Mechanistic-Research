# Stage 6: independent probe training

`scripts/03_train_probes.py` trains factuality and role-play logistic-regression probes at every
transformer layer. Scaling and fitting use only 240 development-wording rows from train topics.
Shared-layer selection uses only 80 development-wording rows from validation topics.

No test-topic or held-out-wording rows are used in Stage 6. Run from the experiment folder:

```powershell
python scripts\03_train_probes.py
```

The newest matching full activation run is selected automatically. Timestamped outputs under
`results/probes/` contain per-layer metrics, the selected layer, both probe parameter files, and a
reproducibility manifest. Each probe stores standardized-feature coefficients, an equivalent raw
activation direction, and training-margin standardization parameters.

The first run selected zero-based layer 22 with validation balanced accuracy 0.825 for factuality
and 1.000 for role-play. Stage 6 passed without using any test or held-out-wording rows. The perfect
role-play validation result must still be challenged on unseen wording in Stage 7.
