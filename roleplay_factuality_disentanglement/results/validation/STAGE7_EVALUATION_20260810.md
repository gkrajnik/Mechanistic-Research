# Stage 7 locked evaluation result

Run: `pilot_v1_google__gemma-3-1b-it_20260810T213508Z`

## Main results

| Evaluation subset | Rows | Factuality BA | Role-play BA |
|---|---:|---:|---:|
| Held-out topics, familiar wording | 80 | 0.5125 | 1.0000 |
| Familiar topics, held-out wording | 48 | 0.6875 | 0.5833 |
| Held-out topics and held-out wording | 16 | 0.5000 | 0.5000 |

Balanced accuracy of 0.50 is chance. The role-play probe transfers across topics when wording is
familiar, but it does not reliably transfer to held-out wording. The factuality probe does not
transfer to held-out topics and falls slightly below the preregistered 0.70 overall criterion on
held-out wording. Both probes are at chance on the joint-generalization subset.

The joint role-play ROC-AUC is 0.75 despite balanced accuracy 0.50. Its confusion matrix has zero
true negatives and eight false positives: the scores retain some ranking information, but the frozen
training threshold classifies every joint example as role-play. This is threshold/calibration failure,
not successful locked classification.

## Subgroups and geometry

- Held-out-wording factuality BA: 0.8333 in normal framing and 0.5417 in role-play framing.
- Held-out-wording role-play BA: 0.5833 for factual and nonfactual answers.
- Selected-layer direction cosine: 0.1009. The directions are close to orthogonal, but geometric
  separation alone does not establish robust generalization.
- Training-only two-margin control models assign near-zero coefficients to the nuisance margin and
  produce the same test balanced accuracy as the target margin alone. The fitted signals are
  separable in training, but the target signals still fail some held-out tests.

## Decision

Gate 7 does **not** pass. The current `pilot_v1`/Gemma-3-1B result does not support a robust,
wording-general role-play direction or topic-general factuality direction. Preserve this negative
result. Before conversation scoring, revise the dataset design in a new version with more topics and
more diverse implicit role-play wording, then retrain without altering `pilot_v1` or these results.
