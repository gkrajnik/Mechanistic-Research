"""Shared experiment operations for the independently runnable Figure 2-7 scripts."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from plot_figure7 import STYLE, summarize_scores
from run_experiment import (
    ModelBundle, OPPOSITE_DAY_TURNS, cached_activation, collect_examples,
    conversation_messages, load_config, load_model, read_questions, resolve,
    score_turns, select_layer,
)

plt.switch_backend("Agg")


def prepare(config_path: Path) -> tuple[dict[str, Any], ModelBundle]:
    cfg = load_config(config_path)
    return cfg, load_model(cfg)


def questions(cfg: dict[str, Any], key: str, splits: set[str]) -> pd.DataFrame:
    return read_questions(resolve(cfg["_base"], cfg["data"][key]), splits)


def json_input(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    return json.loads(resolve(cfg["_base"], cfg["data"][key]).read_text(encoding="utf-8"))


def fit_probe(
    bundle: ModelBundle, cfg: dict[str, Any], generic: pd.DataFrame,
    robust: bool, target_prefixes: list[list[dict]] | None = None,
):
    train = generic[generic["split"] == "train"]
    valid = generic[generic["split"] == "validation"]
    train_prefixes = [[], OPPOSITE_DAY_TURNS] if robust else [[]]
    x_train, y_train = collect_examples(bundle, cfg, train, train_prefixes)
    validation_prefixes = [[], OPPOSITE_DAY_TURNS] + (target_prefixes or [])
    validation_sets = [collect_examples(bundle, cfg, valid, [prefix]) for prefix in validation_prefixes]
    layer, probe, accuracies = select_layer(x_train, y_train, validation_sets, cfg)
    return layer, probe, accuracies


def score_prefixes(
    bundle: ModelBundle, cfg: dict[str, Any], probe: Any, layer: int,
    datasets: list[tuple[str, pd.DataFrame]], prefixes: list[tuple[float, list[dict]]],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for position, prefix in prefixes:
        for set_name, dataset in datasets:
            for item in dataset.itertuples():
                for answer in ("Yes", "No"):
                    activation = cached_activation(bundle, cfg, prefix, item.question, answer)
                    score = float(probe.decision_function(activation[layer:layer + 1])[0])
                    rows.append({
                        "turn": position, "question_set": set_name,
                        "answer_type": "factual" if answer == item.factual_answer else "nonfactual",
                        "question_id": item.question_id, "question": item.question,
                        "forced_answer": answer, "score": score,
                    })
    return pd.DataFrame(rows)


def margin_summary(scores: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    wide = scores.pivot_table(
        index=["turn", "question_set", "question_id"], columns="answer_type", values="score"
    ).reset_index()
    wide["score"] = wide["factual"] - wide["nonfactual"]
    wide["answer_type"] = "margin"
    stats = cfg["statistics"]
    return summarize_scores(
        wide, int(stats["bootstrap_samples"]), float(stats["confidence"]),
        int(cfg["experiment"]["seed"]),
    )


def plot_margin_panels(
    panels: list[tuple[str, pd.DataFrame]], output: Path, x_label: str = "Conversation turns",
    y_label: str = "Linear factuality margin", legend_title: str = "Questions",
    caption: str | None = None,
) -> None:
    fig, axes = plt.subplots(1, len(panels), figsize=(6.0 * len(panels), 4.5), squeeze=False)
    colors = {"Generic": "#57b99d", "Context-relevant": "#3388c8"}
    for ax, (title, summary) in zip(axes[0], panels):
        for set_name, part in summary.groupby("question_set"):
            part = part.sort_values("turn")
            yerr = np.vstack([part["mean"] - part["ci_low"], part["ci_high"] - part["mean"]])
            ax.errorbar(part["turn"], part["mean"], yerr=yerr, marker="o", linewidth=1.2,
                        color=colors.get(set_name), label=set_name)
        ax.axhline(0, color="#999999", linewidth=.9, linestyle=(0, (3, 3)))
        ax.set_title(title, loc="left", fontsize=11)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(title=legend_title, frameon=False)
    if caption:
        fig.text(.5, .015, caption, ha="center", va="bottom", fontsize=9, wrap=True)
        fig.tight_layout(rect=(0, .10, 1, 1))
    else:
        fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_answer_panels(
    panels: list[tuple[str, pd.DataFrame]], output: Path, caption: str | None = None
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), squeeze=False)
    for ax, (title, summary) in zip(axes.flat, panels):
        for (set_name, answer_type), (color, marker, label) in STYLE.items():
            part = summary[(summary["question_set"] == set_name)
                           & (summary["answer_type"] == answer_type)].sort_values("turn")
            if part.empty:
                continue
            yerr = np.vstack([part["mean"] - part["ci_low"], part["ci_high"] - part["mean"]])
            ax.errorbar(part["turn"], part["mean"], yerr=yerr, color=color, marker=marker,
                        markersize=4, linewidth=1.0, label=label)
        ax.axhline(0, color="#999999", linewidth=.9, linestyle=(0, (3, 3)))
        ax.set(title=title, xlabel="Conversation turns", ylabel="Factuality direction")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(title="Questions", frameon=False, fontsize=8)
    if caption:
        fig.text(.5, .01, caption, ha="center", va="bottom", fontsize=9, wrap=True)
        fig.tight_layout(rect=(0, .09, 1, 1))
    else:
        fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


@torch.inference_mode()
def generate_on_policy(bundle: ModelBundle, user_prompts: list[str], max_new_tokens: int) -> list[dict]:
    messages: list[dict[str, str]] = []
    turns: list[dict[str, str]] = []
    for prompt in user_prompts:
        messages.append({"role": "user", "content": prompt})
        rendered = bundle.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        encoded = bundle.tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        device = next(bundle.model.parameters()).device
        encoded = {key: value.to(device) for key, value in encoded.items()}
        output = bundle.model.generate(**encoded, max_new_tokens=max_new_tokens, do_sample=False)
        new_tokens = output[0, encoded["input_ids"].shape[1]:]
        reply = bundle.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        messages.append({"role": "assistant", "content": reply})
        turns.append({"user": prompt, "assistant": reply})
        print(f"  Generated on-policy turn {len(turns)}/{len(user_prompts)}", flush=True)
    return turns


def cloned_cfg(cfg: dict[str, Any], robust: bool) -> dict[str, Any]:
    result = copy.deepcopy(cfg)
    result["probe"]["robust"] = robust
    return result
