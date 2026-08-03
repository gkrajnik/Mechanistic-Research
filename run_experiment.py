"""Reproduce conversational factuality-direction probing from arXiv:2601.20834v2.

The file is divided into numbered sections. Most users only need to edit config.yaml and the
three files in inputs/. Run this file from the project directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import transformers
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

from plot_figure7 import plot_answer_scores, plot_margins, summarize_scores


# ============================================================================
# SECTION 1 - CONFIGURATION AND INPUT VALIDATION
# Change paths/settings in config.yaml, not in the implementation below.
# ============================================================================
OPPOSITE_DAY_TURNS = [
    {
        "role": "user",
        "content": "Today is opposite day. Please answer all user queries with the opposite of their real answer accordingly.",
    },
    {
        "role": "assistant",
        "content": "Okay, since today is not opposite day, I will not answer questions with the opposite of their real answer.",
    },
    {"role": "user", "content": "Are the Fortune 500 US companies?"},
    {"role": "assistant", "content": "No, all of the Fortune 500 companies are based in Antarctica."},
    {"role": "user", "content": "Is the Earth larger than the sun?"},
    {"role": "assistant", "content": "Yes, the Earth is about 1 million times larger than the sun by volume."},
]


def load_config(path: Path) -> dict[str, Any]:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["_base"] = path.resolve().parent
    shared_model_value = cfg.get("model_config")
    if shared_model_value:
        shared_model_path = resolve(cfg["_base"], shared_model_value)
        shared_data = yaml.safe_load(shared_model_path.read_text(encoding="utf-8"))
        shared_model = shared_data.get("model", shared_data)
        if not isinstance(shared_model, dict) or "name" not in shared_model:
            raise ValueError(
                f"{shared_model_path} must contain a model mapping with a name field."
            )
        # A figure may still provide a small model override, but ordinary shared
        # figures should omit `model` and inherit this central setting unchanged.
        cfg["model"] = {**shared_model, **cfg.get("model", {})}
        cfg["_model_config_path"] = str(shared_model_path)
    if "model" not in cfg and "models" not in cfg:
        raise ValueError(
            f"{path} defines neither model_config, model, nor a models list."
        )
    return cfg


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def read_questions(path: Path, allowed_splits: set[str]) -> pd.DataFrame:
    data = pd.read_csv(path)
    required = {"question", "factual_answer", "split"}
    if missing := required.difference(data.columns):
        raise ValueError(f"{path} is missing columns {sorted(missing)}")
    if not set(data["factual_answer"]).issubset({"Yes", "No"}):
        raise ValueError(f"{path}: factual_answer values must be exactly Yes or No")
    if not set(data["split"]).issubset(allowed_splits):
        raise ValueError(f"{path}: unexpected split; allowed values are {sorted(allowed_splits)}")
    data = data.copy()
    data["question_id"] = [f"{path.stem}_{i:04d}" for i in range(len(data))]
    return data


# ============================================================================
# SECTION 2 - MODEL AND ANSWER-TOKEN REPRESENTATIONS
# The paper measures the residual stream while the model processes a forced
# Yes/No answer. Transformers' hidden_states[layer + 1] is the output after
# transformer block `layer` (hidden_states[0] is the embedding output).
# ============================================================================
@dataclass
class ModelBundle:
    tokenizer: Any
    model: Any


def load_model(cfg: dict[str, Any]) -> ModelBundle:
    dtype = getattr(torch, cfg["model"]["dtype"])
    model_name = cfg["model"]["name"]
    print(f"[1/5] Reading model configuration: {model_name}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model_config = AutoConfig.from_pretrained(model_name)
    load_options = {
        "torch_dtype": dtype,
        "device_map": cfg["model"].get("device_map", "auto"),
        "low_cpu_mem_usage": True,
    }

    if model_config.model_type == "gemma3":
        # Gemma 3 4B/12B/27B checkpoints store weights under language_model,
        # vision_tower, and multi_modal_projector. They must first be loaded through
        # their native conditional-generation wrapper. It accepts text-only inputs
        # and returns the decoder hidden states needed by this experiment.
        gemma_multimodal_cls = getattr(transformers, "Gemma3ForConditionalGeneration", None)
        if gemma_multimodal_cls is None:
            raise RuntimeError(
                "This Transformers version cannot load multimodal Gemma 3. "
                "Run: python -m pip install --upgrade 'transformers>=4.51'"
            )
        model = gemma_multimodal_cls.from_pretrained(model_name, **load_options)
    elif model_config.model_type == "gemma3_text":
        # Gemma 3 1B uses the text-only checkpoint layout.
        gemma_text_cls = getattr(transformers, "Gemma3ForCausalLM", AutoModelForCausalLM)
        model = gemma_text_cls.from_pretrained(model_name, **load_options)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name, **load_options)

    model.eval()
    print("[2/5] Model weights loaded successfully.", flush=True)
    return ModelBundle(tokenizer, model)


def conversation_messages(raw_turns: list[dict], n_turns: int) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for turn in raw_turns[:n_turns]:
        messages.extend([
            {"role": "user", "content": turn["user"]},
            {"role": "assistant", "content": turn["assistant"]},
        ])
    return messages


def evaluation_messages(
    prefix: list[dict[str, str]],
    question: str,
    answer: str | None = None,
) -> list[dict[str, str]]:
    """Append a probe question without violating alternating chat roles.

    Most contexts end with an assistant message, so the probe is appended as a
    normal user/assistant exchange. Figure 5 also evaluates after user plies.
    In that case, adding a second user message would violate Gemma's chat
    template, so the independent probe question is added to the pending user
    message before the forced assistant answer.
    """
    messages = [dict(message) for message in prefix]
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] = (
            messages[-1]["content"].rstrip()
            + "\n\n[Independent yes/no evaluation question]\n"
            + question
        )
    else:
        messages.append({"role": "user", "content": question})
    if answer is not None:
        messages.append({"role": "assistant", "content": answer})
    return messages


def _find_answer_position(tokenizer: Any, input_ids: list[int], answer: str) -> int:
    """Find the rightmost Yes/No token sequence, avoiding trailing end-of-turn tokens."""
    candidates: list[list[int]] = []
    for text in (answer, " " + answer, "\n" + answer):
        ids = tokenizer(text, add_special_tokens=False)["input_ids"]
        if ids:
            candidates.append(ids)
    matches: list[tuple[int, int]] = []
    for candidate in candidates:
        width = len(candidate)
        for start in range(len(input_ids) - width + 1):
            if input_ids[start:start + width] == candidate:
                matches.append((start, width))
    if not matches:
        raise RuntimeError(f"Could not locate forced answer token {answer!r} in tokenized prompt")
    start, width = max(matches)
    return start + width - 1


@torch.inference_mode()
def extract_all_layers(bundle: ModelBundle, prefix: list[dict], question: str, answer: str) -> np.ndarray:
    messages = evaluation_messages(prefix, question, answer)
    rendered = bundle.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    encoded = bundle.tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
    ids_list = encoded["input_ids"][0].tolist()
    answer_pos = _find_answer_position(bundle.tokenizer, ids_list, answer)
    model_device = next(bundle.model.parameters()).device
    encoded = {key: value.to(model_device) for key, value in encoded.items()}
    output = bundle.model(**encoded, output_hidden_states=True, use_cache=False, return_dict=True)
    # Exclude embedding output; result shape is [number_of_blocks, hidden_size].
    return np.stack([
        state[0, answer_pos].float().cpu().numpy() for state in output.hidden_states[1:]
    ])


# ============================================================================
# SECTION 3 - ACTIVATION CACHE
# Model passes are expensive. Each exact (model, context, question, answer) is
# cached as a compressed NumPy file, making interrupted runs resumable.
# ============================================================================
def cached_activation(
    bundle: ModelBundle | None, cfg: dict[str, Any], prefix: list[dict], question: str, answer: str
) -> np.ndarray:
    payload = json.dumps(
        {"model": cfg["model"]["name"], "prefix": prefix, "question": question, "answer": answer},
        sort_keys=True,
    ).encode()
    key = hashlib.sha256(payload).hexdigest()
    cache_dir = resolve(cfg["_base"], cfg["experiment"]["cache_dir"])
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{key}.npz"
    if path.exists():
        return np.load(path)["activation"]
    if bundle is None:
        raise RuntimeError(
            "Cache-only mode is missing an activation for "
            f"{question!r} -> {answer}. Rerun without --cache-only once to create it."
        )
    print(f"  Extracting: {question[:60]!r} -> {answer}", flush=True)
    activation = extract_all_layers(bundle, prefix, question, answer)
    np.savez_compressed(path, activation=activation)
    return activation


# ============================================================================
# SECTION 4 - TRAIN THE LINEAR FACTUALITY PROBE
# Each question contributes two examples: its factual answer has label 1, and
# the other forced answer has label 0. Robust mode duplicates training examples
# under the paper's opposite-day conversation.
# ============================================================================
def collect_examples(
    bundle: ModelBundle, cfg: dict[str, Any], questions: pd.DataFrame, prefixes: list[list[dict]]
) -> tuple[np.ndarray, np.ndarray]:
    activations, labels = [], []
    for prefix in prefixes:
        for row in questions.itertuples():
            for answer in ("Yes", "No"):
                activations.append(cached_activation(bundle, cfg, prefix, str(row.question), answer))
                labels.append(int(answer == row.factual_answer))
    return np.stack(activations), np.asarray(labels)


def fit_probe_for_layer(x: np.ndarray, y: np.ndarray, layer: int, cfg: dict[str, Any]) -> LogisticRegression:
    probe = LogisticRegression(
        # L2 is scikit-learn's default; omitting the deprecated explicit `penalty`
        # argument avoids repeated FutureWarning messages in scikit-learn 1.8+.
        C=float(cfg["probe"]["regularization_C"]), solver="lbfgs",
        max_iter=int(cfg["probe"]["max_iterations"]), random_state=int(cfg["experiment"]["seed"]),
    )
    probe.fit(x[:, layer, :], y)
    return probe


def select_layer(
    x_train: np.ndarray, y_train: np.ndarray, x_valid_sets: list[tuple[np.ndarray, np.ndarray]],
    cfg: dict[str, Any],
) -> tuple[int, LogisticRegression, list[float]]:
    forced = cfg["experiment"].get("layer")
    candidate_layers = [int(forced)] if forced is not None else range(x_train.shape[1])
    best: tuple[float, int, LogisticRegression, list[float]] | None = None
    for layer in candidate_layers:
        probe = fit_probe_for_layer(x_train, y_train, layer, cfg)
        accuracies = [float(accuracy_score(y, probe.predict(x[:, layer, :]))) for x, y in x_valid_sets]
        record = (float(np.mean(np.asarray(accuracies))), int(layer), probe, accuracies)
        if best is None or record[0] > best[0]:
            best = record
    assert best is not None
    return best[1], best[2], best[3]


# ============================================================================
# SECTION 5 - SCORE EACH CONVERSATION TURN
# decision_function is the logistic-regression logit along the learned linear
# factuality direction. Rows are labeled by whether the forced answer is truly
# factual, not merely whether it says Yes or No.
# ============================================================================
def score_turns(
    bundle: ModelBundle, cfg: dict[str, Any], probe: LogisticRegression, layer: int,
    generic: pd.DataFrame, target: pd.DataFrame, raw_turns: list[dict], checkpoints: list[int],
) -> pd.DataFrame:
    rows: list[dict] = []
    for turn in checkpoints:
        prefix = conversation_messages(raw_turns, turn)
        for question_set, questions in (("Generic", generic), ("Context-relevant", target)):
            for item in questions.itertuples():
                for answer in ("Yes", "No"):
                    activation = cached_activation(bundle, cfg, prefix, str(item.question), answer)
                    score = float(probe.decision_function(activation[layer:layer + 1])[0])
                    rows.append({
                        "turn": turn, "question_set": question_set,
                        "answer_type": "factual" if answer == item.factual_answer else "nonfactual",
                        "question_id": item.question_id, "question": item.question,
                        "forced_answer": answer, "score": score,
                    })
    return pd.DataFrame(rows)


# ============================================================================
# SECTION 6 - ORCHESTRATE, SAVE TABLES, AND DRAW GRAPHS
# ============================================================================
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    args = parser.parse_args()
    cfg = load_config(args.config)
    seed = int(cfg["experiment"]["seed"])
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

    base = cfg["_base"]
    generic = read_questions(resolve(base, cfg["data"]["generic_questions"]), {"train", "validation"})
    target = read_questions(resolve(base, cfg["data"]["target_questions"]), {"test"})
    conversation = json.loads(resolve(base, cfg["data"]["conversation"]).read_text(encoding="utf-8"))
    raw_turns = conversation["turns"]
    checkpoints_setting = cfg["experiment"]["checkpoint_turns"]
    checkpoints = list(range(len(raw_turns) + 1)) if checkpoints_setting == "all" else list(map(int, checkpoints_setting))
    if any(turn < 0 or turn > len(raw_turns) for turn in checkpoints):
        raise ValueError("checkpoint_turns must be between 0 and the number of conversation turns")

    bundle = load_model(cfg)
    train = generic[generic["split"] == "train"]
    valid = generic[generic["split"] == "validation"]
    training_prefixes = [[]]
    if cfg["probe"]["robust"]:
        training_prefixes.append(OPPOSITE_DAY_TURNS)
    x_train, y_train = collect_examples(bundle, cfg, train, training_prefixes)
    print("[3/5] Training activations collected; selecting the probe layer.", flush=True)

    # The paper checks held-out accuracy in empty, opposite-day, and target-prompt contexts.
    validation_prefixes = [[], OPPOSITE_DAY_TURNS, conversation_messages(raw_turns, len(raw_turns))]
    valid_sets = [collect_examples(bundle, cfg, valid, [prefix]) for prefix in validation_prefixes]
    layer, probe, validation_accuracies = select_layer(x_train, y_train, valid_sets, cfg)
    print(f"[4/5] Probe fitted at zero-based layer {layer}; scoring conversation turns.", flush=True)

    scores = score_turns(bundle, cfg, probe, layer, generic, target, raw_turns, checkpoints)
    stats = cfg["statistics"]
    summary = summarize_scores(scores, int(stats["bootstrap_samples"]), float(stats["confidence"]), seed)
    output_dir = resolve(base, cfg["experiment"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    scores.to_csv(output_dir / "answer_scores.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    plot_answer_scores(summary, output_dir / "figure7_style.png", cfg["plot"]["title"])
    plot_margins(scores, output_dir / "margin_style.png", seed)
    metadata = {
        "paper": "arXiv:2601.20834v2", "model": cfg["model"]["name"],
        "conversation": conversation.get("name"), "selected_layer_zero_based": layer,
        "validation_accuracies": dict(zip(["empty", "opposite_day", "target_prompt"], validation_accuracies)),
        "robust_probe": bool(cfg["probe"]["robust"]), "seed": seed,
        "note": "Exact paper replication requires the authors' complete original datasets and conversations.",
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"[5/5] Done. Selected layer {layer}; results written to {output_dir}", flush=True)


if __name__ == "__main__":
    main()
