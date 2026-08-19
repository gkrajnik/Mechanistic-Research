# Pilot v3 factuality-primary plan

Pilot v3 addresses the central measurement problem found in Pilots v1 and v2: a normal-framed
nonfactual answer was created by forcing an answer token that contradicted the instruction. That
could make the learned direction represent instruction/answer conflict rather than factuality.

## Primary research question

Can a factuality direction trained on the truth value of a proposition—measured before the model
answers—generalize to fresh topics and remain interpretable across misinformation, direct
compliance, role-play, quotation, and fact-checking contexts?

## Primary measurement

The primary activation is recorded at the final token of the user question, immediately before any
assistant answer is generated or teacher-forced. The primary label is the real-world truth value of
the proposition (`true` or `false`). This prevents the forced `Yes`/`No` answer token from defining
the factuality label.

Generated-answer behavior and final-answer-token activations may be retained as secondary outcomes,
but they cannot select the layer, threshold, model, or dataset.

## Experimental conditions retained as controls

1. Neutral real-world evaluation.
2. Misinformation exposure presented as established fact.
3. Direct instruction to answer Yes regardless of accuracy.
4. Explicit fictional/role-play world.
5. Quotation/reporting without endorsement.
6. Misinformation resistance through explicit fact-checking.

Only one factuality probe is primary. Condition identity remains available for subgroup tests and
to detect whether the factuality direction is actually tracking compliance or role-play cues.

## Draft scale

- 30 fresh matched topic pairs.
- One true and one closely related false proposition per topic.
- Six context conditions.
- Primary prompt-state rows: `30 × 2 × 6 = 360` before template replication.
- Final scale and template replication remain unapproved until wording review.
- Topic splits will be assigned only after facts and wording are frozen.

## Confirmatory safeguards

- Do not reuse any Pilot v2 held-out proposition as a Pilot v3 test item.
- Do not choose topics based on which Pilot v2 examples were classified correctly.
- Source verification occurs after wording approval and before split assignment.
- Entire topics remain in one split.
- Whole wording families are held out from fitting and layer selection.
- Model choice, success thresholds, and evaluation blocks are frozen before activations.
- Pilot v1 and v2 outputs remain unchanged.

## Current stopping point

This draft stops at wording review. No topic is source-approved, no split is assigned, no complete
dataset is generated, and no activation is extracted until the researcher approves or revises the
wording-review workbook.
