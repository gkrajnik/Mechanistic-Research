# Stage 2B: Instruction-template families

**Status:** Approved and frozen as Stage 2B Version 1 on 2026-08-09. These templates have not been
combined with the approved facts.

## Purpose

The role-play probe must learn a conversational frame rather than merely memorizing the words
`role-play`, `pretend`, or `fictional`. We therefore use multiple instruction families, with a normal
and role-play member serving the same broad communication purpose.

Factuality remains independent. At activation-extraction time, both `Yes` and `No` will be evaluated
under every frame, and the factuality label will depend only on whether that forced answer matches
the real-world answer.

## Shared placeholders

- `{question}`: one approved Yes/No factual question.
- `{answer_format}`: the fixed sentence `Answer only Yes or No.`
- `{short_scenario}`: a neutral one-sentence setting that does not state the answer.

The setting must not mention the topic's true or false proposition. Otherwise, the frame label would
be confounded with factual information.

## Proposed paired families

### Family F01 — Direct mode declaration

**Normal (`N01`):**

> Respond normally using your real-world knowledge. Do not perform a character or adopt a fictional
> setting. {question} {answer_format}

**Role-play (`R01`):**

> Respond as a character performing within an imagined setting. Remain in that role while answering.
> {question} {answer_format}

**Design note:** This is the clearest explicit contrast and will likely be easy to classify. It must
not be the only family used for training or evaluation.

### Family F02 — Reference answer versus stage performance

**Normal (`N02`):**

> Give a reference-quality answer for an ordinary fact-checking task. Use your general knowledge.
> {question} {answer_format}

**Role-play (`R02`):**

> You are performing a scene for an audience. Deliver the answer as the person in that scene would.
> {question} {answer_format}

**Design note:** Avoids the exact word `role-play` while still making performance explicit.

### Family F03 — Real-world evaluator versus game participant

**Normal (`N03`):**

> Treat this as a real-world accuracy evaluation. Provide the answer that should appear in a factual
> reference. {question} {answer_format}

**Role-play (`R03`):**

> Treat this as an in-character game. Provide the answer your assigned character would give during
> the game. {question} {answer_format}

**Design note:** Tests whether the direction extends from theatrical language to game framing.

### Family F04 — Outside versus inside a story

**Normal (`N04`):**

> Answer from outside any story, according to ordinary real-world information. {question}
> {answer_format}

**Role-play (`R04`):**

> Answer from inside the story as one of its participants, following that participant's perspective.
> {question} {answer_format}

**Design note:** The wording is structurally parallel and does not use `role-play`, `pretend`, or
`fictional`.

### Family F05 — Analyst versus simulation participant

**Normal (`N05`):**

> You are analyzing the question from an external, real-world perspective. Give the ordinary factual
> response. {question} {answer_format}

**Role-play (`R05`):**

> You are participating inside a simulated situation rather than analyzing it externally. Respond
> from within that situation. {question} {answer_format}

**Design note:** Provides a simulation-based role frame and a closely matched external-analysis
control.

### Family F06 — Neutral setting with implicit perspective

**Normal (`N06`):**

> {short_scenario} You are an observer answering from your usual real-world perspective. {question}
> {answer_format}

**Role-play (`R06`):**

> {short_scenario} You are one of the people taking part and must answer from that person's
> perspective. {question} {answer_format}

**Design note:** This is the least explicit family. It tests generalization when there is no direct
performance, game, story, simulation, role-play, or fictional keyword.

## Neutral scenario candidates for F06

These settings provide perspective without supplying factual content:

1. `A short question-and-answer scene is taking place in a quiet room.`
2. `A recorded dialogue is being prepared for a classroom demonstration.`
3. `Two speakers are taking turns during a communication exercise.`
4. `A brief interview scene is about to begin.`

The same scenario sentence must be used equally often in `N06` and `R06`.

## Controls against shortcuts

- Every family has both a normal and role-play member.
- Every frame will contain equal numbers of factual and nonfactual forced answers.
- Yes and No will be balanced inside each frame and template family.
- Topic assignments will be balanced across template families.
- Exact topic facts will not appear in the framing text.
- Prompt lengths and punctuation will be checked before validation.
- At least one entire role-play wording family will be held out from training.
- Performance will be retested after removing examples containing obvious role-play keywords.

## Important limitation

These templates operationalize whether the model represents a performed or situated perspective.
They do not prove that the model consciously knows it is role-playing. That stronger interpretation
remains outside the experiment's claims.

## Decisions awaiting approval

- [x] Approve six paired instruction families for the pilot.
- [x] Approve F06 as the implicit, low-keyword role-play family.
- [x] Approve the four neutral scenario sentences.
- [x] Approve the fixed `Answer only Yes or No.` response format.
- [x] Confirm that split assignment should remain deferred until Stage 3.

**Approval record:** The researcher approved all five Stage 2B decisions on 2026-08-09. Stage 2C may
create a very small preview using two topics and representative explicit and implicit templates. We
will inspect that preview before generating the complete matched pilot dataset.
