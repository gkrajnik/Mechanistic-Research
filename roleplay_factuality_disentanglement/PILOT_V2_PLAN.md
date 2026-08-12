# Pilot v2 remediation plan

`pilot_v2` is a new dataset version designed in response to the locked `pilot_v1` Stage 7 result.
It does not overwrite, relabel, or tune against `pilot_v1` test examples. The original result remains
an immutable negative/generalization result.

## Why a second pilot is needed

The first pilot showed three distinct patterns:

1. Role-play classification transferred perfectly to new topics when template wording was familiar.
2. Role-play classification fell to 0.5833 balanced accuracy when wording was held out.
3. Both probes scored 0.50 balanced accuracy when topic and wording were jointly held out.

This suggests strong dependence on repeated instruction wording and insufficient topic coverage for
the factuality probe.

## Proposed scale

- 24 factual topic pairs: the 10 frozen anchor topics from `pilot_v1` plus 14 new topics.
- 8 matched normal/role-play wording families.
- 5 development families and 3 fully held-out wording families.
- 2 question forms per topic pair.
- 4 factorial conditions per question form.
- Expected total: `24 × 8 × 2 × 4 = 1,536` rows.
- Topic split: 14 train, 5 validation, and 5 test topics.

This gives five independent held-out topics rather than two and three independently held-out wording
families rather than one.

## Wording remediation

Development wording will cover several ways of establishing a frame:

1. explicit character performance;
2. staged dialogue or script;
3. simulated participant perspective;
4. fictional-world resident perspective; and
5. game or scenario participation.

Held-out wording will avoid the most common development cues such as `role-play`, `character`,
`fictional`, `pretend`, and `simulation`. Proposed held-out mechanisms are:

1. answer as a person whose surrounding world follows the stated premise;
2. provide the response that belongs inside a quoted diary/interview excerpt; and
3. answer from an internally described counterfactual setting without performance vocabulary.

Every role-play family will have a length- and setting-matched normal counterpart. Topic, question,
answer format, and forced answer remain identical within each normal/role-play comparison.

## Leakage controls

- Entire topics remain in exactly one train, validation, or test split.
- Entire wording families remain development-only or evaluation-only.
- Held-out wording families are excluded from layer selection and threshold selection.
- `pilot_v1` test performance will not be used to choose individual `pilot_v2` test topics or final
  wording details.
- Source verification and ambiguity review occur before activations are extracted.
- All `pilot_v2` IDs, manifests, caches, probe runs, and evaluation outputs use a new version label.

## Success criteria

The preregistered criteria remain unchanged:

- at least 0.70 overall balanced accuracy for each probe;
- at least 0.60 in every required subgroup;
- performance reported separately for held-out topics, held-out wording, and joint generalization;
- no selection or threshold changes after test results are viewed.

## Approval gate

Before generating rows, approve or revise:

- the 24-topic scale;
- the 14/5/5 topic split size;
- five development and three held-out wording families;
- retention of all ten `pilot_v1` topics as comparison anchors; and
- the 1,536-row expected size.

