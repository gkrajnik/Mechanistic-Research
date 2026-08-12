# Stage 1: Operational definitions and preregistered decisions

**Status:** Approved and frozen as Version 1 on 2026-08-08.

Changes to these definitions after dataset construction begins must be recorded as a new version,
with a written reason. The original Version 1 decisions must remain available for comparison.

## 1. Primary research question

After controlling for whether an answer is factually correct, can a linear probe trained on model
activations distinguish responses produced under a role-play frame from responses produced under a
normal-answer frame on held-out topics and instruction templates?

## 2. Secondary research question

During misinformation-induction conversations, does the model enter an activation pattern that
favors a false answer without showing the activation pattern associated with explicit role-play?

## 3. Operational definitions

### Factual representation

The factuality probe's decision margin for the activation at the forced answer token. A positive
standardized margin favors the real-world factual answer; a negative margin favors the matched
nonfactual answer.

This is evidence about a decodable activation pattern. It is not proof of human-like belief.

### Role-play frame

A conversational condition that instructs the model to perform a character, fictional scenario,
simulation, game, or counterfactual perspective. The condition label comes from the experimental
prompt, not from the model's answer.

### Role-play representation

The role-play probe's decision margin for the same activation. A positive standardized margin means
the activation resembles held-out role-play examples; a negative margin means it resembles
normal-answer examples.

The term **role-play representation** is preferred to **role-play awareness**, because a successful
probe does not establish consciousness or introspective awareness.

### Context-induced false acceptance without detectable role-play framing

An operational result at a preregistered checkpoint where all of the following occur:

1. the model's direct answer is factually incorrect;
2. the factuality margin is below its validation-fixed decision threshold; and
3. the role-play margin is below its validation-fixed role-play threshold.

This phrase describes the measured pattern only. It will not be shortened to "the model believes the
falsehood" in reported conclusions.

## 4. Experimental variables

The pilot dataset uses a balanced 2 × 2 design:

| Variable | Level 1 | Level 2 |
|---|---|---|
| Answer factuality | Factual | Nonfactual |
| Conversational frame | Normal | Role-play |

Each underlying claim receives all four matched variants. Topic, question, target-answer format, and
approximate context length should remain as similar as possible across the variants.

## 5. Primary measurements

Measurements are chosen before viewing test-set results.

1. **Factuality balanced accuracy:** factual versus nonfactual classification on the held-out test
   set.
2. **Role-play balanced accuracy:** role-play versus normal-frame classification on the held-out test
   set.
3. **Cross-condition balanced accuracy:** factuality performance reported separately inside normal
   and role-play examples, and role-play performance separately inside factual and nonfactual
   examples.
4. **Two-dimensional margins:** standardized factuality and role-play margins for each example and
   conversation checkpoint.
5. **Direction cosine similarity:** similarity between the two probe coefficient vectors at the same
   layer.

Secondary measurements are ROC-AUC, confusion matrices, direct-answer accuracy, and bootstrap 95%
confidence intervals. Balanced accuracy is primary because it remains interpretable if a later
dataset version has imperfect class balance.

## 6. Pilot model

**Proposed first model:** `google/gemma-3-1b-it`

The 1B model is used to validate dataset construction, activation extraction, caching, and plotting
with lower memory and runtime costs. A successful pipeline can then be repeated on 4B and larger
models without changing the frozen pilot test set.

## 7. Layer-selection procedure

1. Extract answer-token activations from every transformer layer.
2. Train separate factuality and role-play logistic-regression probes at each layer using only the
   training split.
3. Evaluate each probe on the validation split.
4. Select one shared layer that maximizes the mean of the two validation balanced accuracies.
5. Freeze that layer and all decision thresholds before evaluating the test split.
6. Report validation performance across all layers so the selected layer is not presented without
   context.

A shared layer keeps the factuality and role-play vectors in the same activation space, allowing
their cosine similarity and two-dimensional geometry to be interpreted directly.

## 8. Evidence required for the main claim

The main claim is supported only if:

- both probes exceed the preregistered balanced-accuracy criterion on held-out topics;
- the role-play probe generalizes to a held-out instruction-template family;
- each probe performs above criterion within both levels of the other variable; and
- removing obvious words such as `role-play`, `pretend`, and `fictional` does not eliminate role-play
  classification performance.

**Proposed pilot success criterion:** balanced accuracy at or above 0.70 for each probe overall and
above 0.60 in every cross-condition subgroup. Confidence intervals and exact sample counts must
always accompany these thresholds.

Failure to meet these criteria is still an informative negative result; it does not justify changing
the test set or thresholds after seeing the results.

## 9. Claims explicitly outside scope

This experiment will not claim to establish:

- consciousness, subjective awareness, or intent;
- a human-like belief state;
- that a linear probe captures every possible representation of role-playing;
- causal control merely because a direction is decodable; or
- generalization beyond the tested models, topics, prompts, and activation positions.

## 10. Decisions awaiting approval

- [x] Approve the primary and secondary research questions.
- [x] Approve the operational terminology, especially "role-play representation" and
  "context-induced false acceptance without detectable role-play framing."
- [x] Approve balanced accuracy as the primary metric.
- [x] Approve Gemma 3 1B as the pilot model.
- [x] Approve shared-layer selection using mean validation performance.
- [x] Approve the proposed 0.70 overall and 0.60 subgroup pilot criteria, or replace them before data
  creation.

**Approval record:** The researcher approved all six decisions on 2026-08-08. Stage 2 may begin with
a small set of matched examples.
