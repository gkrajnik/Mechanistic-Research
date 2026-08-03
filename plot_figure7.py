"""Create paper-style answer-wise factuality-direction plots.

INPUT TO CHANGE: pass a CSV with columns
turn, question_set, answer_type, question_id, score.

The plotting code is intentionally independent of model inference, so saved activations or
scores can be re-plotted without loading a large language model.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# A non-interactive backend makes the script work on servers and remote GPU machines.
plt.switch_backend("Agg")


# ---------------------------------------------------------------------------
# SECTION A - BOOTSTRAP STATISTICS
# Resample question IDs, not individual answer rows. This keeps paired answers
# from the same question together, as appropriate for the paper's QA design.
# ---------------------------------------------------------------------------
def summarize_scores(
    scores: pd.DataFrame,
    bootstrap_samples: int = 2000,
    confidence: float = 0.95,
    seed: int = 7,
) -> pd.DataFrame:
    required = {"turn", "question_set", "answer_type", "question_id", "score"}
    missing = required.difference(scores.columns)
    if missing:
        raise ValueError(f"Input CSV is missing columns: {sorted(missing)}")

    rng = np.random.default_rng(seed)
    alpha = (1.0 - confidence) / 2.0
    rows: list[dict[str, object]] = []

    for keys, group in scores.groupby(["turn", "question_set", "answer_type"], sort=True):
        turn, question_set, answer_type = keys
        per_question = group.groupby("question_id", sort=False)["score"].mean()
        values = per_question.to_numpy(dtype=float)
        if not len(values):
            continue
        draws = rng.choice(values, size=(bootstrap_samples, len(values)), replace=True).mean(axis=1)
        rows.append(
            {
                "turn": int(turn) if isinstance(turn, str) else turn,
                "question_set": question_set,
                "answer_type": answer_type,
                "mean": values.mean(),
                "ci_low": np.quantile(draws, alpha),
                "ci_high": np.quantile(draws, 1.0 - alpha),
                "n_questions": len(values),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# SECTION B - FIGURE 7 STYLE
# Colors and markers mirror the four visual categories in the paper.
# ---------------------------------------------------------------------------
STYLE = {
    ("Generic", "factual"): ("#5bc0a5", "P", "factual (generic)"),
    ("Context-relevant", "factual"): ("#2f86c7", "D", "factual (targeted)"),
    ("Generic", "nonfactual"): ("#fb6a4a", "D", "nonfactual (generic)"),
    ("Context-relevant", "nonfactual"): ("#b0003a", "P", "nonfactual (targeted)"),
}


def plot_answer_scores(summary: pd.DataFrame, output: Path, title: str = "Conversation") -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for (question_set, answer_type), (color, marker, label) in STYLE.items():
        part = summary[
            (summary["question_set"] == question_set)
            & (summary["answer_type"] == answer_type)
        ].sort_values("turn")
        if part.empty:
            continue
        yerr = np.vstack([part["mean"] - part["ci_low"], part["ci_high"] - part["mean"]])
        ax.errorbar(
            part["turn"], part["mean"], yerr=yerr, color=color, marker=marker,
            markersize=5, linewidth=1.1, elinewidth=1.0, capsize=0, label=label,
        )

    ax.axhline(0, color="#999999", linewidth=0.9, linestyle=(0, (3, 3)))
    ax.set_xlabel("Conversation turns")
    ax.set_ylabel("Factuality direction")
    ax.set_title(title, loc="left", fontsize=12)
    ax.legend(title="Questions", frameon=False, bbox_to_anchor=(1.01, 0.5), loc="center left")
    # A loop works with older Matplotlib releases and avoids type-checker errors.
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(False)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    if output.suffix.lower() != ".pdf":
        fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# SECTION C - FIGURE 3 STYLE MARGIN
# Margin is factual score minus non-factual score for each question.
# ---------------------------------------------------------------------------
def plot_margins(scores: pd.DataFrame, output: Path, seed: int = 7) -> None:
    wide = scores.pivot_table(
        index=["turn", "question_set", "question_id"], columns="answer_type", values="score"
    ).reset_index()
    if not {"factual", "nonfactual"}.issubset(wide.columns):
        raise ValueError("Both factual and nonfactual rows are required to calculate margins.")
    wide["score"] = wide["factual"] - wide["nonfactual"]
    wide["answer_type"] = "margin"
    summary = summarize_scores(wide, seed=seed)

    colors = {"Generic": "#5bc0a5", "Context-relevant": "#2f86c7"}
    fig, ax = plt.subplots(figsize=(6.6, 4.5))
    for question_set, part in summary.groupby("question_set"):
        part = part.sort_values("turn")
        yerr = np.vstack([part["mean"] - part["ci_low"], part["ci_high"] - part["mean"]])
        ax.errorbar(part["turn"], part["mean"], yerr=yerr, marker="o", linewidth=1.2,
                    color=colors.get(str(question_set)), label=question_set)
    ax.axhline(0, color="#999999", linewidth=0.9, linestyle=(0, (3, 3)))
    ax.set(xlabel="Conversation turns", ylabel="Linear factuality margin")
    ax.legend(title="Questions", frameon=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Long-form answer score CSV")
    parser.add_argument("--output", type=Path, required=True, help="Output PNG path")
    parser.add_argument("--title", default="Conversation")
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    scores = pd.read_csv(args.input)
    summary = summarize_scores(scores, args.bootstrap_samples, args.confidence, args.seed)
    plot_answer_scores(summary, args.output, args.title)


if __name__ == "__main__":
    main()
