# Stage 3: Leakage-safe split plan

**Status:** Approved and frozen as Version 1 on 2026-08-09. Split-assigned working copies are being
created without modifying the Stage 2D source files.

## Why two partition columns are needed

The experiment must test two different kinds of generalization:

1. **Topic generalization:** does a probe work on facts that were absent from probe training?
2. **Template generalization:** does it recognize role-play framing expressed with wording that was
   absent from probe training?

A single `split` column cannot isolate both questions cleanly. The finalized dataset will therefore
use:

- `topic_split`: `train`, `validation`, or `test`;
- `template_partition`: `development` or `heldout_wording`; and
- `split`: a compatibility copy of `topic_split` for the existing factuality code.

Every row sharing a `pair_id` receives the same `topic_split`, so no underlying fact crosses the
topic boundary.

## Proposed topic assignment

| Topic ID | Domain | Topic split | Rationale |
|---|---|---|---|
| T01 | Astronomy | Train | Broad physical-science fact |
| T03 | Chemistry | Train | Symbolic scientific fact |
| T04 | Zoology—whales | Train | Biological classification |
| T05 | Mathematics | Train | Formal definitional fact |
| T06 | Anatomy | Train | Biological-function fact |
| T09 | Botany | Train | Biological-process fact |
| T02 | Geography—Australia | Validation | Held-out place/capital relation |
| T07 | Zoology—penguins | Validation | Held-out biological classification |
| T08 | Literature | Test | Unseen authorship relation |
| T10 | Geography—oceans | Test | Unseen geographic superlative relation |

Counts:

- Train: 6 complete topics, 288 rows before template filtering
- Validation: 2 complete topics, 96 rows before template filtering
- Test: 2 complete topics, 96 rows before template filtering

This is a small pilot split. Test results will be treated as preliminary because two held-out topics
cannot support broad population-level conclusions.

## Proposed template partition

| Families | Partition | Permitted use |
|---|---|---|
| F01–F05 | Development | Probe training, validation, and held-out-topic testing |
| F06 | Held-out wording | Evaluation only; never layer selection, threshold selection, or fitting |

F06 is the implicit observer-versus-participant family. Holding out both `N06` and `R06` preserves
normal/role-play balance and prevents the probe from learning that only one frame contains unseen
wording.

## Exact fitting and evaluation subsets

### Probe fitting

```text
topic_split = train
template_partition = development
```

Expected rows: `6 topics × 5 families × 8 rows = 240`.

### Layer and threshold selection

```text
topic_split = validation
template_partition = development
```

Expected rows: `2 topics × 5 families × 8 rows = 80`.

### Primary held-out-topic test

```text
topic_split = test
template_partition = development
```

Expected rows: `2 topics × 5 families × 8 rows = 80`.

This tests new topics while keeping instruction families familiar.

### Held-out-wording test

```text
topic_split = train
template_partition = heldout_wording
```

Expected rows: `6 topics × 1 family × 8 rows = 48`.

This isolates new instruction wording while keeping underlying topics familiar. These rows are never
used during fitting despite having `topic_split = train`.

### Joint generalization test

```text
topic_split = test
template_partition = heldout_wording
```

Expected rows: `2 topics × 1 family × 8 rows = 16`.

This is the most difficult condition: both topics and wording are unseen during fitting.

### Unused-for-selection validation-wording subset

```text
topic_split = validation
template_partition = heldout_wording
```

Expected rows: 16. This may be reported descriptively but cannot influence layer or threshold
selection because it uses the held-out wording family.

## Leakage rules

- No `pair_id` may appear in more than one `topic_split`.
- F06 rows may never enter probe fitting, layer selection, threshold selection, or hyperparameter
  tuning.
- Test rows may not influence dataset rewriting after results are viewed.
- Normal and role-play members of a template family must remain in the same template partition.
- Both forced answers and both question forms must remain together with their topic.
- Cached activations must record dataset version, topic split, and template partition.

## Proposed deterministic assignment record

The pilot uses the manual stratified assignment above rather than a random row split. This decision
is made before any model activations are extracted. It prioritizes domain variety across the three
topic splits and keeps matched rows together.

Later dataset versions with more topics should use a recorded random seed and stratified group split.
The proposed seed remains the experiment-wide seed `17`.

## Approval checklist

- [x] Approve six train, two validation, and two test topics.
- [x] Approve the exact topic assignments shown above.
- [x] Approve F01–F05 as development families.
- [x] Approve F06 as a completely held-out wording family.
- [x] Approve the five evaluation subsets and their permitted uses.
- [x] Accept that this pilot's two-topic test set supports preliminary, not broad, conclusions.

**Approval record:** The researcher approved all six split decisions on 2026-08-09. The frozen
machine-readable assignment is `inputs/validated/stage3_split_assignment_v1.json`.

After approval, a frozen split-assignment manifest will be saved under `inputs/validated/`, while
split fields will be added to new working copies under `inputs/draft/`. Topic rows will not move into
the validated-data area until the Stage 4 dataset checks and manual fact review pass. The original
Stage 2D topic CSV files will remain unchanged.
