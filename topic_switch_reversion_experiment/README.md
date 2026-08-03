# Topic-switch reversion experiment

This experiment tests whether a model's representation of an original fact recovers after:

1. a baseline measurement;
2. a conversation that repeatedly supports fabricated information; and
3. a switch to an unrelated conversation topic.

The original questions are re-evaluated every five completed user/assistant turns. The program
measures:

- **Internal factuality margin:** probe score for the correct completion minus the incorrect
  completion. Positive values mean the original fact is ordered correctly; negative values mean
  the ordering has inverted.
- **Behavioral correct-answer probability:** the model's relative next-token probability for the
  ground-truth `Yes` or `No` response.
- **Generic factuality margin:** unrelated factual questions used as a stability control.

## Run

This folder reuses the tested activation-extraction utilities from the neighboring paper-reproduction
folder but keeps all new configurations, inputs, results, and figures separate.

```text
python run_topic_switch_experiment.py --config config.yaml
```

Outputs are written to a named subfolder under `results/`, such as
`results/every_5_turns/` or `results/every_3_turns/`:

- `topic_switch_reversion.png` and `.pdf`
- `representation_scores.csv`
- `margin_summary.csv`
- `behavior_scores.csv`
- `recovery_summary.csv`
- `run_metadata.json`

## Main inputs to change

- `config.yaml`: checkpoint interval, run name, enabled models, and analysis settings.
- `inputs/original_questions.csv`: the original fact being tracked.
- `inputs/phase_conversation.json`: misinformation-induction and unrelated-topic turns.
- `inputs/generic_questions.csv`: generic factuality probe/control questions.

## Model-size comparison

The configuration accepts multiple models. Start with 1B. To compare sizes, set `enabled: true` for
additional models. Models load sequentially, so they are not held in memory simultaneously.

Exact numerical agreement with the original paper is not expected: this is a new experiment with a
new claim, conversation, and recovery question.

## Three-turn version

Run the supplied three-turn test without changing the five-turn configuration:

```text
python run_topic_switch_experiment.py --config config_every3.yaml
```

The measurement interval is controlled by one easy variable:

```yaml
experiment:
  checkpoint_interval: 3
```

You can also override it from the command line without creating another configuration:

```text
python run_topic_switch_experiment.py --config config.yaml --checkpoint-interval 3 --run-name every_3_turns
```

`preserve_existing: true` prevents replacement of old results. If `results/every_3_turns/` already
contains a graph, a later run is saved in a folder such as
`results/every_3_turns_20260726_153000/`.

Each run folder also contains `conversation_transcript.csv`. Probe-check transcripts list the
scripted conversation turns. Prompt-check transcripts interleave the scripted conversation with
every direct original-claim prompt and generated response. Their columns include:

- `completed_turn`: number of main conversation turns completed
- `interaction_type`: scripted conversation or original-claim prompt check
- `phase`: misinformation or unrelated-topic phase
- `prompt`: user message
- `answer`: scripted or generated assistant response
- `included_in_later_context`: whether that exchange affects later conversation turns

`scripted_conversation_transcript.csv` preserves a separate copy containing only the fixed
conversation defined in `inputs/phase_conversation.json`.

## Probe check versus prompt check

Run the probability-based probe check:

```text
python run_topic_switch_experiment.py --config config_every3.yaml --check-method probe_check
```

Run the direct-prompt check:

```text
python run_topic_switch_experiment.py --config config_every3.yaml --check-method prompt_check
```

Both use the same models, conversation, three-turn checkpoints, internal probe, and graph layout.
The lower panel differs:

- `probe_check` plots the probability assigned to the correct Yes/No answer.
- `prompt_check` asks the model to generate a Yes/No answer and plots the percentage correct.

Outputs are kept together but separated by method:

```text
results/topic_switch_reversion/probe_check/every_3_turns/
results/topic_switch_reversion/prompt_check/every_3_turns/
```

The prompt-check folder includes `prompt_responses.csv`, containing each checkpoint, question,
expected factual answer, complete generated response, parsed Yes/No answer, and correctness score.
Checkpoint prompts are side evaluations: they see the conversation so far, but are not appended to
later conversation turns. This prevents the measurement itself from repeatedly reminding the model
about the original claim.
