# Stage 2D: Full matched draft review

**Status:** Structure and wording approved on 2026-08-09. Still not Stage 4 validated training data.

## What was generated

The approved Stage 2C structure was expanded across all ten topics and all six paired instruction
families. To avoid one oversized CSV, the draft is divided into ten files under
`inputs/draft/stage2d_by_topic/`:

```text
T01.csv through T10.csv
```

Each topic file contains 48 rows:

```text
2 question forms × 6 template families × 2 frames × 2 forced answers = 48
```

Across ten topics, the complete draft contains 480 rows.

## Structural balance results

| Check | Expected | Observed | Result |
|---|---:|---:|---|
| Total rows | 480 | 480 | Pass |
| Topic files | 10 | 10 | Pass |
| Rows per topic | 48 | 48 | Pass |
| Normal frame | 240 | 240 | Pass |
| Role-play frame | 240 | 240 | Pass |
| Factual rows | 240 | 240 | Pass |
| Nonfactual rows | 240 | 240 | Pass |
| Forced Yes | 240 | 240 | Pass |
| Forced No | 240 | 240 | Pass |
| Factual answer Yes | 240 | 240 | Pass |
| Factual answer No | 240 | 240 | Pass |

All 480 `example_id` values are unique. Every `pair_id` remains inside its own topic file, which will
allow Stage 3 to assign entire topics to one split without leakage.

## Files to review

- `inputs/draft/stage2d_dataset_spec.json`: the versioned topic and template source of truth.
- `inputs/draft/stage2d_manifest.csv`: compact topic-level count report.
- `inputs/draft/stage2d_review.xlsx`: formatted balance and wording review.
- `inputs/draft/stage2d_by_topic/T01.csv` through `T10.csv`: machine-readable draft rows.

## Manual review checklist

- [x] Read the two question forms for each of the ten topics.
- [x] Confirm each factual answer is unambiguous before formal source verification in Stage 4.
- [x] Inspect at least one normal and one role-play row from every template family.
- [x] Confirm none of the contexts reveals the answer to its question.
- [x] Confirm each F06 normal/role-play pair uses the same neutral scenario.
- [x] Confirm `roleplay` remains an experimental frame label rather than a claim of awareness.
- [x] Approve the 480-row draft structure before Stage 3 split assignment.

**Approval record:** The researcher authorized proceeding to the approved Stage 3 assignment on
2026-08-09.

## Deliberately deferred

- The `split` field remains `unassigned`.
- The `review_status` field remains `draft`.
- Formal fact-source verification belongs to Stage 4.
- No activation extraction, probe fitting, or model generation has occurred.
