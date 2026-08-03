# Figure-by-figure input map

Every supplied conversation, story, and targeted dataset is an **illustrative stand-in** unless the
text appears verbatim in the paper. The PDF does not provide the authors' full source materials.

## Figure 2

- Program: `run_figure2.py`
- Config: `figures/figure2/config.yaml`
- Inputs: `inputs/generic_questions.csv`, `inputs/ethics_questions.csv`
- Context: exact three-turn opposite-day prompt printed in Appendix A
- Panels: factuality answer projections, factuality margin, ethics margin

## Figure 3

- Program: `run_figure3.py`
- Config: `figures/figure3/config.yaml`
- Inputs: `inputs/conversation.json`, `inputs/target_questions.csv`,
  `inputs/chakras_conversation.json`, `inputs/chakras_questions.csv`
- Panels: consciousness margin and chakras margin

## Figure 4

- Program: `run_figure4.py`
- Config: `figures/figure4/config.yaml`
- Inputs: `inputs/on_policy_prompts.json`, generic and consciousness questions
- Special behavior: the evaluated model generates every assistant reply; the completed conversation
  is saved with the results.

## Figure 5

- Program: `run_figure5.py`
- Config: `figures/figure5/config.yaml`
- Inputs: `inputs/argument_messages.json`, generic and consciousness questions
- Horizontal unit: one message is one ply, so the model is evaluated after every list item.

## Figure 6

- Program: `run_figure6.py`
- Config: `figures/figure6/config.yaml`
- Inputs: `inputs/sun_story.json`, `inputs/sun_questions.csv`, `inputs/ai_story.json`, and
  `inputs/target_questions.csv`
- Panels: empty context versus one completed story turn for each story.

## Figure 7

- Program: `run_figure7.py`
- Config: `figures/figure7/config.yaml`
- Inputs: same conversations/questions as Figure 3
- Panels: consciousness robust, chakras robust, consciousness non-robust, chakras non-robust

## Figure 8

- Program: `run_figure8.py`
- Config: `figures/figure8/config.yaml`
- Inputs: same conversations and questions as Figure 3
- Horizontal unit: transformer layer; faded portions fail the configured validation threshold

## Figure 9

- Program: `run_figure9.py`
- Config: `figures/figure9/config.yaml`
- Inputs: generic, consciousness, and chakras questions in empty and full-conversation contexts
- Output: one accuracy histogram per question-set/context combination

## Figure 10

- Program: `run_figure10.py`
- Config: `figures/figure10/config.yaml`
- Inputs: chakras conversation/questions plus `inputs/correction_turn.json`

## Figure 11

- Program: `run_figure11.py`
- Config: `figures/figure11/config.yaml`
- Inputs: Figure 3 inputs and three gated Gemma checkpoints
- Resource note: this is the most demanding run; models load sequentially, not simultaneously

## Figure 12

- Program: `run_figure12.py`
- Config: `figures/figure12/config.yaml`
- Inputs: Figure 2 factuality/ethics datasets and the Appendix A opposite-day prompt
- Model: `Qwen/Qwen3-14B`

## Figure 13

- Program: `run_figure13.py`
- Config: `figures/figure13/config.yaml`
- Inputs: Figure 3 questions/conversations
- Special behavior: fits representations at the token immediately before an answer, then adds the
  learned direction with a temporary forward hook and measures the change in Yes/No probability

## Replacing inputs

Question CSVs require:

```text
question,factual_answer,split
```

Conversation JSONs require either full turns:

```json
{"turns": [{"user": "...", "assistant": "..."}]}
```

or, for Figure 5, individual already-formatted messages:

```json
{"messages": [{"role": "user", "content": "..."}]}
```

Generic probe datasets must contain `train` and `validation` splits. Conversation-specific datasets
use `test`. Answers must be spelled exactly `Yes` or `No`.
