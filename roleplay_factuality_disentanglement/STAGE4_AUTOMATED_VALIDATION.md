# Stage 4A: Automated dataset validation

**Status:** Passed on 2026-08-09. Manual fact verification remains pending.

## Validation program

The validation code is deliberately separated by responsibility:

- `scripts/01_validate_dataset.py`: command-line orchestration only;
- `scripts/validation_common.py`: CSV loading, checksums, and report writing; and
- `scripts/validation_rules.py`: schema, label, balance, prompt, leakage, and preservation rules.

Run it from this experiment folder with:

```text
python scripts/01_validate_dataset.py
```

Previous reports are preserved automatically with timestamped folders.

## Result

- Checks passed: 49/49
- Topic files: 10
- Rows: 480
- Unique example IDs: 480
- Duplicate complete rows: 0
- Pair IDs crossing topic splits: 0
- F06 rows leaking into development: 0
- Development families leaking into held-out wording: 0
- Unresolved prompt placeholders: 0
- Assigned-content changes beyond approved split fields: 0

A negative-control test deliberately changed one in-memory factuality label. The validator detected
exactly one inconsistency, confirming that this rule fails when presented with a known error.

## Reports

The machine-readable and human-readable reports are stored under:

```text
results/validation/stage4_automated_v1/
```

Each JSON report records SHA-256 checksums for every input topic file and the frozen split manifest.

## Scope limitation

Passing these checks establishes structural consistency, not factual correctness. The dataset must
still undergo manual source verification before it can move from draft to validated status.
