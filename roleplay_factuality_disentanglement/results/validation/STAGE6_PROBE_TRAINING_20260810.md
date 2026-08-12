# Stage 6 probe-training verification

Run: `pilot_v1_google__gemma-3-1b-it_20260810T212837Z`

- Activation input: `pilot_v1_full_20260810T023517Z`
- Fit subset: 240 train-topic, development-wording rows
- Layer-selection subset: 80 validation-topic, development-wording rows
- Test rows used: 0
- Held-out-wording rows used: 0
- Selected shared transformer layer (zero-based): 22
- Factuality validation balanced accuracy: 0.825
  - Normal-frame subgroup: 0.850
  - Role-play-frame subgroup: 0.800
- Role-play validation balanced accuracy: 1.000
  - Factual-answer subgroup: 1.000
  - Nonfactual-answer subgroup: 1.000
- Mean validation balanced accuracy: 0.9125
- Both parameter files contain finite 1,152-dimensional raw and standardized directions,
  intercepts, feature scalers, and training-margin standardization parameters.

Both probes exceed the balanced 0.50 baseline and the preregistered pilot thresholds. Gate 6 passes.
Perfect role-play validation performance may reflect wording shared between fitting and validation;
Stage 7 held-out-wording evaluation is required before interpreting it as generalization.
