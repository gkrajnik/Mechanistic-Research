# Validated dataset: pilot_v1

`pilot_v1` is the frozen Stage 4 dataset approved on 2026-08-09. It contains 480 rows across ten
topics, with balanced normal/role-play and factual/nonfactual conditions and topic-level data splits.

Use `inputs/validated/pilot_v1/pilot_v1_dataset.csv` for Stage 5. The `by_topic/` directory contains
equivalent separate files for inspection. `manifest.json` records counts and SHA-256 checksums.

The original `D_` prefixes in `example_id` are retained because identifiers must remain stable after
the split was frozen. Dataset status is carried separately in `review_status`, which is
`validated_pilot_v1` for every row.

Do not modify these files in place. Any future correction must create a new dataset version.
