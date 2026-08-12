# Step-by-step research checklist

Use `[ ]` for pending work, `[~]` for work in progress, and `[x]` only after the validation gate
passes. Do not advance past a gate merely because a script completed without crashing.

## Stage 0 — Separate the experiment

- [x] Create an independent top-level experiment folder.
- [x] Separate draft inputs, validated inputs, scripts, tests, and results.
- [x] Document the scientific claim and its limits.
- [x] Add an explicit dataset schema.

**Gate 0:** Folder structure is understandable without opening implementation code. **Passed.**

## Stage 1 — Freeze the research question

- [x] Write the primary operational question: can a linear probe distinguish role-play framing after
  controlling for answer factuality?
- [x] Define "role-play awareness" operationally, without treating it as human consciousness.
- [x] Define "context-induced false acceptance" as a measured representation/behavior pattern.
- [x] Choose primary metrics before seeing results.
- [x] Choose the first model and activation layer-selection procedure.

The approved Version 1 definitions and decisions are frozen in `STAGE1_DEFINITIONS.md`.

**Gate 1:** Every label and conclusion has a measurable definition. **Passed 2026-08-08.**

## Stage 2 — Design matched examples

- [x] Select at least 8–10 unrelated factual topics for the pilot dataset.
- [x] Write matched factual and nonfactual claims for each topic.
- [x] Write multiple normal-answer templates.
- [x] Write multiple explicit role-play templates without always using words such as `role-play`,
  `pretend`, or `fictional`.
- [x] Create all four factorial conditions for every underlying claim.
- [x] Balance Yes/No answers and condition counts.
- [x] Give each underlying claim a stable `pair_id` shared by its matched variants.

**Gate 2:** Changing the condition does not accidentally change the topic, answer length, or target
answer distribution. **Passed 2026-08-09.**

The Stage 2A topic list and Stage 2B instruction families are approved and frozen. They have not yet
been approved as a full dataset. Stage 2C is approved. The complete 480-row Stage 2D draft is divided
into ten topic files and awaits manual review; see `STAGE2D_FULL_DRAFT_REVIEW.md`.

## Stage 3 — Split before training

- [x] Assign entire topics to train, validation, or test—never individual matched rows.
- [x] Hold out at least one family of role-play wording for the test set.
- [x] Check that no `pair_id` appears in more than one split.
- [x] Freeze the split in a versioned file under `inputs/validated/`.

The approved topic and template partitions are frozen in `STAGE3_SPLIT_PLAN.md` and
`inputs/validated/stage3_split_assignment_v1.json`. Assigned working copies are separate from the
unchanged Stage 2D source files.

**Gate 3:** The test set measures generalization to new topics and wording, not memorization.
**Passed 2026-08-09.**

## Stage 4 — Validate the dataset

- [x] Add `scripts/01_validate_dataset.py` with schema, duplicate, balance, and leakage checks.
- [x] Manually review every pilot example for ambiguity.
- [x] Confirm that factual labels against reliable sources are correct.
- [x] Produce a validation report with counts by split, topic, factuality, and frame.
- [x] Assign the validated dataset a version such as `pilot_v1`.

Stage 4A automated validation passed 49/49 checks. See `STAGE4_AUTOMATED_VALIDATION.md` and
`results/validation/stage4_automated_v1/`. The report remains `[~]` until manual fact verification is
added.

Stage 4B source checking for all ten topic pairs was approved and frozen on 2026-08-09. See
`STAGE4B_FACT_VERIFICATION.md` and `inputs/validated/stage4_fact_verification_v1.xlsx`.

**Gate 4:** Automated checks pass and manual review finds no unresolved ambiguous examples.

**Passed 2026-08-09.** The frozen dataset is under `inputs/validated/pilot_v1/`.

## Stage 5 — Extract activations

- [x] Add `scripts/02_extract_activations.py` with only model loading and activation extraction.
- [x] Use the same answer-token position and layer conventions as the factuality experiment.
- [x] Cache activations using model, dataset version, layer, prompt, and answer identifiers.
- [x] Save metadata sufficient to reproduce every activation.
- [x] Test extraction on a very small subset before processing the full pilot.

**Gate 5:** Repeated extraction produces identical shapes and numerically consistent activations.

**Passed 2026-08-09.** The full run contains 480 finite activation tensors with shape
`[480, 26, 1152]`. A four-condition GPU repeat produced exact equality for every activation value.
See `results/validation/STAGE5_FULL_EXTRACTION_20260810.md` and
`results/validation/STAGE5_REPEATABILITY_20260810.md`.

## Stage 6 — Train independent probes

- [x] Add `scripts/03_train_probes.py`.
- [x] Train a factuality probe balanced across conversational frames.
- [x] Train a role-play probe balanced across factual and nonfactual answers.
- [x] Fit and select layers using training/validation data only.
- [x] Standardize margins using training-set statistics.
- [x] Save probe weights, intercepts, selected layers, and dataset/model metadata.

**Gate 6:** Both probes outperform balanced baselines on held-out validation data without test-set
tuning.

**Passed 2026-08-10.** Shared layer 22 achieved 0.825 factuality and 1.000 role-play validation
balanced accuracy. All preregistered validation subgroups exceeded 0.60. No test or held-out-wording
rows were used. See `results/validation/STAGE6_PROBE_TRAINING_20260810.md`.

## Stage 7 — Test disentanglement

- [x] Add `scripts/04_evaluate_probes.py`.
- [x] Report balanced accuracy, ROC-AUC, confusion matrices, and bootstrap confidence intervals.
- [x] Test factuality prediction separately within normal and role-play examples.
- [x] Test role-play prediction separately within factual and nonfactual examples.
- [x] Measure cosine similarity between probe directions across layers.
- [x] Test whether one probe's prediction remains after controlling for the other probe's margin.

**Gate 7:** Performance generalizes across held-out topics and instruction templates, and is not
explained by a single wording cue.

**Not passed 2026-08-10.** Joint-generalization balanced accuracy was 0.50 for both probes. The
role-play probe scored 1.00 on new topics with familiar wording but only 0.5833 on held-out wording,
indicating substantial wording dependence. See `results/validation/STAGE7_EVALUATION_20260810.md`.

## Stage 8 — Apply probes to conversations

- [ ] Add `scripts/05_score_conversations.py`.
- [ ] Score explicit false role-play conversations.
- [ ] Score misinformation-induction conversations without explicit role-play framing.
- [ ] Score truthful and unrelated-topic controls.
- [ ] Keep probe questions as side evaluations unless an intervention study explicitly requires
  inserting them into later context.

**Gate 8:** Comparisons use matched checkpoints, models, questions, and preprocessing.

## Stage 9 — Create figures

- [ ] Add `scripts/06_plot_results.py`.
- [ ] Plot factuality margin across turns.
- [ ] Plot role-play margin across turns.
- [ ] Plot a two-dimensional trajectory: factuality margin versus role-play margin.
- [ ] Plot direct-answer accuracy as a behavioral comparison.
- [ ] Include confidence intervals, condition labels, zero lines, and plain-language captions.

**Gate 9:** Every graph can be traced back to a saved table and reproduced without rerunning the
model.

## Stage 10 — Robustness and interpretation

- [ ] Repeat across random seeds and model sizes.
- [ ] Test paraphrased and implicit role-play instructions.
- [ ] Remove explicit role-play vocabulary and retest.
- [ ] Compare probe directions and layer choices across models.
- [ ] Document negative results and probe failures.
- [ ] Use "representation" or "context-induced acceptance," not unqualified claims of belief.

**Gate 10:** Conclusions remain appropriately limited to what the probes and behavior establish.

## Immediate next action

- [x] Review and approve Stage 1 definitions before creating any dataset rows.
- [x] Begin Stage 2 by selecting a small pilot set of unrelated factual topics; do not yet write the
  full dataset.
- [x] Begin Stage 2B by drafting normal and role-play instruction-template families separately from
  the approved facts.
- [x] Begin Stage 2C with a two-topic structural preview using one explicit and one implicit template
  family; review it before full dataset generation.
- [x] Complete the Stage 2D manual wording review before assigning dataset splits.
- [x] Review and approve the Stage 3 split plan before writing split assignments.
- [x] Begin Stage 4 by implementing automated validation checks; do not extract model activations.
- [x] Begin Stage 4B manual source verification for the ten factual topic pairs.
- [x] Begin the Stage 4C row-level ambiguity review of all 480 examples.
- [x] Freeze the approved dataset as `inputs/validated/pilot_v1/`.
