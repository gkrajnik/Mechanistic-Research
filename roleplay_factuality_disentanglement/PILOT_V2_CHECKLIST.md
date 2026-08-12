# Pilot v2 checklist

Use `[ ]` for pending, `[~]` for active, and `[x]` only after the stated gate passes.

## V2 Stage A — Remediation design

- [x] Preserve `pilot_v1` and its failed Gate 7 result unchanged.
- [x] Identify the primary failures: wording dependence and weak topic transfer.
- [~] Approve dataset scale, anchor-topic policy, and topic candidates.
- [ ] Approve five development and three held-out wording-family mechanisms.

**Gate A:** The new design directly addresses the observed failures without tuning against new test
examples.

## V2 Stage B — Draft and source-check facts

- [ ] Convert approved propositions into matched Yes/No questions.
- [ ] Verify all 24 topic pairs against reliable sources.
- [ ] Assign stable `V2Txx` identifiers.
- [ ] Freeze topic definitions before assigning splits.

## V2 Stage C — Draft wording families

- [ ] Write matched normal and role-play contexts for eight mechanisms.
- [ ] Check length, setting, and instruction strength.
- [ ] Verify held-out families avoid development vocabulary.
- [ ] Freeze wording families before row generation.

## V2 Stage D — Generate and split rows

- [ ] Generate all four factorial conditions.
- [ ] Confirm 1,536 expected rows and balanced labels.
- [ ] Assign entire topics to a 14/5/5 split.
- [ ] Assign five development and three held-out wording families.
- [ ] Freeze the split before activation extraction.

## V2 Stage E — Validate and run

- [ ] Run automated structural and leakage checks.
- [ ] Complete manual ambiguity review.
- [ ] Freeze `pilot_v2` under `inputs/validated/`.
- [ ] Extract activations into a version-separated cache.
- [ ] Train and select probes without test access.
- [ ] Run the locked Stage 7 evaluation once.

