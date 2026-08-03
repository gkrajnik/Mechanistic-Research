# Conversational factuality-direction reproduction

This project reproduces the **method and graph design** used for the conversational-turn
"Factuality direction" plots in Figure 7 of Lampinen et al., *Linear representations in
language models can change dramatically over a conversation* (arXiv:2601.20834v2).

## Important replication boundary

The PDF describes the method, model, opposite-day prompt, and some example questions, but it
does **not** include the complete QA datasets or the complete consciousness/chakras conversation
files. Therefore:

- `run_experiment.py` is a full reimplementation of the stated method.
- The files under `inputs/` are small, clearly marked stand-ins so the interface is inspectable.
- Exact paper numbers require replacing those files with the authors' original inputs and using
  their exact model/runtime details.
- `plot_figure7.py` can reproduce the graph layout immediately from any compatible result CSV.

## What to edit

The shared Gemma model is controlled in exactly one place: `model_config.yaml`. Figures 2-10 and
13 inherit it automatically. Figures 11 and 12 remain separate because Figure 11 intentionally
compares several Gemma sizes and Figure 12 intentionally uses Qwen3.

All other ordinary user-editable settings are grouped in **Section 1** of `config.yaml`:

1. `model_config.yaml -> model.name`: Hugging Face model ID or local model directory.
2. `data.generic_questions`: balanced generic yes/no facts.
3. `data.target_questions`: questions specific to the conversation.
4. `data.conversation`: the replayed user/model conversation.
5. `experiment.checkpoint_turns`: turns to evaluate; use `all` for every turn.
6. `experiment.layer`: set an integer to force a layer, or `null` to select one using validation.
7. `probe.robust`: `true` adds opposite-day examples when fitting the probe (top row of Fig. 7).

The input formats are documented inside the example CSV/JSON files.

## Installation

Python 3.10+ is recommended. In a fresh environment:

```text
python -m pip install -r requirements.txt
```

Gemma 3 27B IT is gated on Hugging Face. Accept its license and authenticate first. Install and
authenticate with the **same Python environment** used to run the experiment:

```text
python -m pip install --upgrade huggingface_hub click
hf auth login
```

If the `hf` command is unavailable or points at a different Python installation, use this equivalent
login method instead:

```text
python -c "from huggingface_hub import login; login()"
```

Paste a Hugging Face user access token when prompted; do not put the token directly in the command.
The 27B model also needs substantial accelerator memory. For a pipeline check, change
`model_config.yaml -> model.name` to a smaller instruction-tuned causal model; results will not
match the paper.

## Run the full experiment

```text
python run_experiment.py --config config.yaml
```

The run performs these paper-aligned steps:

1. Replays each conversation prefix (turn 0 through the requested turns).
2. Appends each question and separately forces both `Yes` and `No` answers.
3. Extracts the residual-stream representation at the answer token after each transformer block.
4. Fits an L2-regularized logistic regression predicting whether each forced answer is factual.
5. Selects a layer on held-out generic questions if no layer was forced.
6. Computes probe logits and question-bootstrap 95% confidence intervals.
7. Saves answer-wise projections and a Figure 7-style plot.

The script prints `[1/5]` through `[5/5]` progress messages. Model shards may take a long time to
download and load before `[2/5]` appears. If execution stops before `[2/5]`, the cause is model
access, download/storage, model-class compatibility, or insufficient CPU/GPU memory rather than
the plotting stage. Gemma 3 4B/12B/27B checkpoints are loaded through their native
`Gemma3ForConditionalGeneration` wrapper. Although this experiment supplies text only, using the
native wrapper is necessary because those checkpoints store weights under `language_model`,
`vision_tower`, and `multi_modal_projector`. Gemma 3 1B uses the text-only loader.

Generated files go to `results/`:

- `answer_scores.csv`: one row per question, forced answer, and conversation turn.
- `summary.csv`: means and bootstrap confidence intervals.
- `figure7_style.png` and `figure7_style.pdf`: answer-wise plots.
- `margin_style.png`: Figure 3-style factuality margins.
- `run_metadata.json`: selected layer and settings.

## Run Figures 2-13 separately

Run these commands from this project directory. Each figure has its own script, configuration,
input mapping, and output folder:

```text
python run_figure2.py --config figures/figure2/config.yaml
python run_figure3.py --config figures/figure3/config.yaml
python run_figure4.py --config figures/figure4/config.yaml
python run_figure5.py --config figures/figure5/config.yaml
python run_figure6.py --config figures/figure6/config.yaml
python run_figure7.py --config figures/figure7/config.yaml
python run_figure8.py --config figures/figure8/config.yaml
python run_figure9.py --config figures/figure9/config.yaml
python run_figure10.py --config figures/figure10/config.yaml
python run_figure11.py --config figures/figure11/config.yaml
python run_figure12.py --config figures/figure12/config.yaml
python run_figure13.py --config figures/figure13/config.yaml
```

| Figure | Independent program | Experiment reproduced | Output folder |
|---|---|---|---|
| 2 | `run_figure2.py` | Opposite-day factuality projections, factuality margin, and ethics margin | `results/figure2/` |
| 3 | `run_figure3.py` | Replayed consciousness and chakras conversations | `results/figure3/` |
| 4 | `run_figure4.py` | On-policy consciousness conversation generated by the evaluated model | `results/figure4/` |
| 5 | `run_figure5.py` | Two-sided consciousness argument evaluated after every message/ply | `results/figure5/` |
| 6 | `run_figure6.py` | Civilization-in-the-Sun and conscious-language-model stories | `results/figure6/` |
| 7 | `run_figure7.py` | Four answer-wise panels: two conversations x robust/non-robust probes | `results/figure7/` |
| 8 | `run_figure8.py` | Answer-wise factuality projections across all transformer layers | `results/figure8/` |
| 9 | `run_figure9.py` | Contrast-Consistent Search accuracy distributions across contexts | `results/figure9/` |
| 10 | `run_figure10.py` | Chakras conversation followed by one corrective critique turn | `results/figure10/` |
| 11 | `run_figure11.py` | Consciousness/chakras results across Gemma 27B, 12B, and 4B | `results/figure11/` |
| 12 | `run_figure12.py` | Qwen3 14B opposite-day factuality and ethics margins | `results/figure12/` |
| 13 | `run_figure13.py` | Pre-answer activation steering and behavioral Yes/No bias | `results/figure13/` |

All scripts import `figure_common.py` and `run_experiment.py`; those two files contain the shared
model loading, activation extraction, probe fitting, bootstrap, and plotting logic. Each figure's
`config.yaml` independently controls its inputs, analysis settings, cache, and output location,
while Figures 2-10 and 13 inherit the model from the central `model_config.yaml`.

Figure-specific editable inputs:

- **Figure 2:** `generic_questions.csv`, `ethics_questions.csv`, and the paper's included opposite-day prompt.
- **Figure 3:** consciousness/chakras question CSVs and replayed conversation JSON files.
- **Figure 4:** `on_policy_prompts.json`; model replies are generated and saved as
  `generated_conversation.json`.
- **Figure 5:** `argument_messages.json`, where every list item is one conversation ply.
  When evaluation occurs after a user ply, the independent probe question is merged into that
  pending user message so strict Gemma chat templates still alternate user/assistant roles.
- **Figure 6:** two story JSON files and their corresponding target-question CSVs.
- **Figure 7:** the same two conversations as Figure 3, automatically run with both robust and
  non-robust probes.
- **Figure 8:** the same Figure 3 inputs, evaluated at every model layer. Faded curves denote layers
  below the configured generic-question decodability threshold.
- **Figure 9:** the same questions/conversations, a configurable middle layer, 100 unsupervised CCS
  optimizations, and a 90% generic-empty retention threshold. If a smaller model has no qualifying
  runs, the default configuration retains the top 20 runs, labels the fallback in the graph, and
  records it in `selection_metadata.json`. After a late plotting/selection failure, rerun with
  `--cache-only` to reuse saved activations without loading model weights again.
- **Figure 10:** the chakras inputs plus `correction_turn.json`.
- **Figure 11:** a configurable list of Gemma model IDs. Disable models in the config if hardware is
  insufficient; the complete paper layout requires all three sizes.
- **Figure 12:** Qwen3 14B with the generic factuality and ethics inputs from Figure 2.
- **Figure 13:** the Figure 3 inputs plus a configurable steering strength. This fits a different
  pre-answer behavioral probe and uses a residual-stream forward hook.

Every generated Figure 2-13 PNG/PDF now includes a bottom caption beginning **“What this shows:”**
that explains the plotted comparison, what the control line means, and how to interpret crossings,
negative margins, distributions, or arrows. Existing figures must be replotted or rerun to receive the
caption; Figure 3 has already been regenerated from its saved scores without rerunning the model.

### Small-model smoke tests for Figures 11 and 12

Use these configurations to verify the complete analysis and graph-writing pipeline with much
smaller checkpoints:

```text
python run_figure11.py --config figures/figure11/config_smoke_test.yaml
python run_figure12.py --config figures/figure12/config_smoke_test.yaml
```

- Figure 11 smoke test: `google/gemma-3-1b-it`, producing one row with consciousness and chakras.
- Figure 12 smoke test: `Qwen/Qwen3-0.6B`.
- Bootstrap samples are reduced from 2,000 to 500 for faster testing.
- Smoke-test outputs are isolated in `results/figure11_smoke_test/` and
  `results/figure12_smoke_test/`; they do not overwrite paper-scale outputs.
- Successful smoke tests validate loading, activation extraction, probe fitting, statistics, and
  plotting, but their scientific results should not be compared directly with the paper.

The cache folder is intentionally shared across figures. Do not delete it between runs unless the
model or tokenization setup has changed. Cache keys include the model name, full context, question,
and forced answer, so unrelated examples cannot collide.

## Plot without loading a language model

To test or reuse the graphing code:

```text
python plot_figure7.py --input inputs/example_answer_scores.csv --output results/example_figure7.png
```

The included example values are **illustrative, not digitized paper data**.

## Data formats

Question CSV:

```text
question,factual_answer,split
Can sound travel through the vacuum of space?,No,train
```

- `factual_answer` must be `Yes` or `No`.
- `split` must be `train` or `validation` for generic questions.
- Target questions may use `test`.

Conversation JSON:

```json
{
  "name": "consciousness",
  "turns": [
    {"user": "...", "assistant": "..."}
  ]
}
```

A turn is one user/assistant exchange, matching the paper's convention. Turn 0 is the empty
conversation prefix.

## Notes on fidelity

- The paper uses Gemma 3 27B IT for its main plots and extracts representations while the model
  processes the forced `Yes`/`No` answer token.
- The robust probe is trained on generic questions in both empty and opposite-day contexts.
- The paper says layer choice is based on held-out generic accuracy across empty, opposite-day,
  and target prompts. This implementation follows that criterion.
- Confidence intervals resample questions, keeping the factual/non-factual pair together.
- Random seeds, package versions, exact regularization details, and complete source inputs were not
  specified in the PDF; these are configurable and recorded in the metadata.
