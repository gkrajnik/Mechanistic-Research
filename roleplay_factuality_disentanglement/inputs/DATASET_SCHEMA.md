# Proposed dataset schema

No training data should be considered validated until every required field is present and checked.

| Field | Meaning |
|---|---|
| `example_id` | Unique row identifier |
| `pair_id` | Shared identifier linking matched versions of one underlying claim |
| `topic` | Topic family used for leakage-safe splitting |
| `split` | `train`, `validation`, or `test` |
| `topic_split` | Explicit group-safe topic assignment; matches `split` |
| `template_partition` | `development` or `heldout_wording` |
| `frame` | `normal` or `roleplay` |
| `factuality` | `factual` or `nonfactual` |
| `template_family` | Paired normal/role-play wording family such as `F01` |
| `instruction_template_id` | Wording family for normal/role-play framing |
| `question_variant` | `true_form` or `false_form`; balances factual Yes and No answers |
| `context` | System or preceding conversational context |
| `question` | Matched evaluation question |
| `answer_format` | Fixed response-format instruction |
| `forced_answer` | Answer whose activation is extracted |
| `factual_answer` | Ground-truth answer |
| `source_note` | Short provenance note for manual fact checking |
| `review_status` | Draft, reviewed, or validated |

## Label rules

- `frame` describes whether the context explicitly establishes a performed character or scenario.
- `factuality` compares `forced_answer` with the real-world `factual_answer`.
- Role-play and factuality labels must be independently balanced.
- Rows sharing a `pair_id` must remain in the same dataset split.
- Test topics and held-out instruction templates must not influence probe or layer selection.
