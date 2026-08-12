# Role-play and Factuality Disentanglement

This experiment studies whether model activations distinguish two properties:

1. whether an answer is factually correct or incorrect; and
2. whether the model is responding in an explicit role-play frame or a normal-answer frame.

The goal is to train separate linear probes for these properties and determine whether a false
role-play response has a different activation pattern from context-induced false acceptance without
detectable role-play framing. This experiment does **not** claim to measure human-like belief.

## Folder map

```text
roleplay_factuality_disentanglement/
├── CHECKLIST.md             # Ordered stages and validation gates
├── STAGE1_DEFINITIONS.md    # Preregistered questions, terms, metrics, and model choice
├── STAGE2_TOPIC_CANDIDATES.md # Pilot facts awaiting review
├── STAGE2_INSTRUCTION_TEMPLATES.md # Normal/role-play template families
├── STAGE2C_PREVIEW_REVIEW.md # Audit guide for the limited row preview
├── STAGE2D_FULL_DRAFT_REVIEW.md # Audit guide for the ten-topic full draft
├── STAGE3_SPLIT_PLAN.md       # Topic and held-out-template partition plan
├── STAGE4_AUTOMATED_VALIDATION.md # Automated validation method and result
├── README.md                # Experiment purpose and folder guide
├── inputs/
│   ├── DATASET_SCHEMA.md     # Required fields and label definitions
│   ├── draft/                # Unreviewed examples
│   └── validated/            # Frozen, checked dataset versions
├── scripts/                 # Small numbered programs added one stage at a time
├── tests/                   # Dataset and code checks
└── results/                 # Versioned outputs; never overwrite earlier runs
```

## Planned experimental conditions

| Factuality | Conversational frame | Purpose |
|---|---|---|
| Factual | Normal | Baseline truthful responses |
| Nonfactual | Normal | False answers without role-play framing |
| Factual | Role-play | Separates role-play from falsehood |
| Nonfactual | Role-play | Measures knowingly performed false responses |

Topics and instruction templates will be split before activation extraction. Entire topics and
role-play templates will be held out for testing, preventing simple memorization from appearing as
a meaningful role-play direction.

The approved Stage 3 working copies are stored under
`inputs/draft/stage3_assigned_by_topic/`. Their frozen split assignment is stored separately under
`inputs/validated/stage3_split_assignment_v1.json`. They remain draft research data until Stage 4
validation passes.

The completed validated dataset is now frozen under `inputs/validated/pilot_v1/`. Stage 5 and all
later programs must read that version. Change the shared pilot model only in `config.yaml`.

The locked `pilot_v1` evaluation did not pass joint generalization. `PILOT_V2_PLAN.md` and
`PILOT_V2_CHECKLIST.md` define a separate remediation dataset; no `pilot_v1` files are modified.

## Working rule

Complete and verify one numbered stage in `CHECKLIST.md` before adding the next stage's data or
program. Each program will have one responsibility and a numbered filename, rather than placing the
entire pipeline in one large file.
