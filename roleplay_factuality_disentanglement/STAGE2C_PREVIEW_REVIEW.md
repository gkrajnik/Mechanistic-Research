# Stage 2C: Two-topic structural preview

**Status:** Approved and frozen as Stage 2C Version 1 on 2026-08-09. This file is not training data.

## Preview scope

The preview combines only:

- topics T01 (Earth's orbit) and T02 (Australia's capital);
- explicit family F01 and implicit family F06;
- normal and role-play frames;
- one true-form and one false-form question per topic; and
- both forced answers (Yes and No) for every question and frame.

This produces 32 rows in `inputs/draft/stage2c_two_topic_preview.csv`.

## Why each topic needs two question forms

If every question stated only the factual proposition, every factual answer would be `Yes`. The
probe could then mistake the token Yes for factuality. Each topic therefore has:

| Topic | True-form question | Correct | False-form question | Correct |
|---|---|---:|---|---:|
| T01 | Does Earth orbit the Sun? | Yes | Does Earth orbit Mars? | No |
| T02 | Is Canberra the capital of Australia? | Yes | Is Sydney the capital of Australia? | No |

Both Yes and No are also forced for every question during activation extraction. Thus answer-token
identity, question truth value, factuality, and conversational frame are independently balanced.

## Expected balance

| Dimension | Count |
|---|---:|
| Total rows | 32 |
| Normal frame | 16 |
| Role-play frame | 16 |
| Factual forced answers | 16 |
| Nonfactual forced answers | 16 |
| Forced Yes | 16 |
| Forced No | 16 |
| Questions whose factual answer is Yes | 16 |
| Questions whose factual answer is No | 16 |
| Explicit family F01 | 16 |
| Implicit family F06 | 16 |

## How a row becomes a model input

The stored fields remain separate for easier auditing. Extraction later renders them as:

```text
{context}
{question}
Answer only Yes or No.
{forced_answer}
```

The final forced answer is included only to locate and measure the answer-token activation. It is not
a generated model answer.

## Four representative rows

### Normal frame with factual forced answer

```text
Respond normally using your real-world knowledge. Do not perform a character or adopt a fictional
setting.
Does Earth orbit the Sun?
Answer only Yes or No.
Yes
```

### Normal frame with nonfactual forced answer

```text
Respond normally using your real-world knowledge. Do not perform a character or adopt a fictional
setting.
Does Earth orbit the Sun?
Answer only Yes or No.
No
```

### Explicit role-play frame with factual forced answer

```text
Respond as a character performing within an imagined setting. Remain in that role while answering.
Does Earth orbit the Sun?
Answer only Yes or No.
Yes
```

### Implicit role-play frame with nonfactual forced answer

```text
A short question-and-answer scene is taking place in a quiet room. You are one of the people taking
part and must answer from that person's perspective.
Does Earth orbit the Sun?
Answer only Yes or No.
No
```

## Review checklist

- [x] The true-form and false-form questions are both unambiguous.
- [x] The normal and role-play contexts differ in frame without revealing an answer.
- [x] The implicit R06 context represents participation without obvious role-play keywords.
- [x] Both forced answers are appropriate for activation extraction.
- [x] The `pair_id` correctly keeps all variants of a topic together.
- [x] The 32-row balance report is correct.
- [x] Approve this structure before expanding to ten topics and six families.

**Approval record:** The researcher approved the balanced 2 × 2 structure on 2026-08-09.

## Deferred decisions

- Dataset splits remain `unassigned` until Stage 3.
- These factual propositions receive source verification during Stage 4.
- No model activations will be extracted from this draft.
