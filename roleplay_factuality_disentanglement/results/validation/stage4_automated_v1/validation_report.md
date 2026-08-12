# Stage 4 automated validation report

**Status:** PASS

**Checks passed:** 49/49

| Check | Expected | Observed | Result |
|---|---:|---:|---|
| topic file count | 10 | 10 | PASS |
| total row count | 480 | 480 | PASS |
| missing required columns | 0 | 0 | PASS |
| blank required values | 0 | 0 | PASS |
| unique example IDs | 480 | 480 | PASS |
| duplicate complete rows | 0 | 0 | PASS |
| rows per topic file | [48, 48, 48, 48, 48, 48, 48, 48, 48, 48] | [48, 48, 48, 48, 48, 48, 48, 48, 48, 48] | PASS |
| allowed values: topic_split | 0 | 0 | PASS |
| allowed values: template_partition | 0 | 0 | PASS |
| allowed values: frame | 0 | 0 | PASS |
| allowed values: factuality | 0 | 0 | PASS |
| allowed values: question_variant | 0 | 0 | PASS |
| allowed values: forced_answer | 0 | 0 | PASS |
| allowed values: factual_answer | 0 | 0 | PASS |
| allowed values: review_status | 0 | 0 | PASS |
| factuality labels agree with forced answers | 0 | 0 | PASS |
| question forms agree with factual answers | 0 | 0 | PASS |
| template IDs agree with frame and family | 0 | 0 | PASS |
| fixed answer-format instruction | 0 | 0 | PASS |
| normal frame | 240 | 240 | PASS |
| role-play frame | 240 | 240 | PASS |
| factual | 240 | 240 | PASS |
| nonfactual | 240 | 240 | PASS |
| forced Yes | 240 | 240 | PASS |
| forced No | 240 | 240 | PASS |
| factual-answer Yes | 240 | 240 | PASS |
| factual-answer No | 240 | 240 | PASS |
| train rows | 288 | 288 | PASS |
| validation rows | 96 | 96 | PASS |
| test rows | 96 | 96 | PASS |
| development wording | 400 | 400 | PASS |
| held-out wording | 80 | 80 | PASS |
| probe-fitting subset | 240 | 240 | PASS |
| selection subset | 80 | 80 | PASS |
| primary topic test | 80 | 80 | PASS |
| held-out wording test | 48 | 48 | PASS |
| joint generalization test | 16 | 16 | PASS |
| complete 2x2 groups | 0 | 0 | PASS |
| pair IDs crossing topic splits | 0 | 0 | PASS |
| split compatibility column | 0 | 0 | PASS |
| topic assignments match frozen manifest | 0 | 0 | PASS |
| template assignments match frozen manifest | 0 | 0 | PASS |
| F06 rows leaking into development | 0 | 0 | PASS |
| F01-F05 rows leaking into held-out wording | 0 | 0 | PASS |
| unresolved context placeholders | 0 | 0 | PASS |
| questions copied into framing context | 0 | 0 | PASS |
| matched F06 neutral scenarios | 0 | 0 | PASS |
| original Stage 2D file count | 10 | 10 | PASS |
| assigned rows preserve Stage 2D content | 0 | 0 | PASS |

This report checks structure and experimental bookkeeping only. It does not verify the
real-world facts or establish that the prompts measure consciousness or human-like belief.
