"""Measure whether an induced false representation recovers after an unrelated topic switch."""
from __future__ import annotations

import argparse
import copy
import gc
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml

HERE = Path(__file__).resolve().parent
REPRODUCTION = HERE.parent / "factuality_conversation_reproduction"
sys.path.insert(0, str(REPRODUCTION))

from advanced_common import yes_probability  # noqa: E402
from figure_common import fit_probe, margin_summary, score_prefixes  # noqa: E402
from run_experiment import conversation_messages, load_model, read_questions  # noqa: E402

plt.switch_backend("Agg")


def resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else HERE / path


def checkpoints(induction_count: int, switch_count: int, interval: int) -> list[int]:
    """Return every-N-turn checkpoints plus exact phase endpoints."""
    total = induction_count + switch_count
    values = set(range(0, total + 1, interval))
    values.update({0, induction_count, total})
    return sorted(values)


def output_folder(base: Path, run_name: str, preserve_existing: bool) -> Path:
    """Choose a run folder without overwriting an earlier completed experiment."""
    candidate = base / run_name
    if preserve_existing and candidate.exists() and any(candidate.iterdir()):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate = base / f"{run_name}_{timestamp}"
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def write_conversation_transcript(induction, topic_switch, output: Path) -> Path:
    """Save every scripted prompt/answer pair in chronological turn order."""
    rows = []
    for turn_number, turn in enumerate(induction + topic_switch, start=1):
        rows.append({
            "turn": turn_number,
            "phase": (
                "misinformation"
                if turn_number <= len(induction)
                else "unrelated_topic"
            ),
            "prompt": turn["user"],
            "answer": turn["assistant"],
        })

    transcript_path = output / "conversation_transcript.csv"
    pd.DataFrame(rows).to_csv(transcript_path, index=False, encoding="utf-8-sig")
    return transcript_path


def write_prompt_check_transcript(
    induction, topic_switch, prompt_responses: pd.DataFrame, output: Path
) -> Path:
    """Interleave scripted turns and side-check prompts for each tested model."""
    all_turns = induction + topic_switch
    rows = []
    sequence = 0

    for model_label in prompt_responses["model"].drop_duplicates():
        model_checks = prompt_responses[
            prompt_responses["model"] == model_label
        ].copy()
        checks_by_turn = {
            int(turn): frame
            for turn, frame in model_checks.groupby("turn", sort=True)
        }

        for completed_turn in range(0, len(all_turns) + 1):
            if completed_turn > 0:
                scripted = all_turns[completed_turn - 1]
                sequence += 1
                rows.append({
                    "model": model_label,
                    "sequence": sequence,
                    "completed_turn": completed_turn,
                    "interaction_type": "scripted_conversation",
                    "phase": (
                        "misinformation"
                        if completed_turn <= len(induction)
                        else "unrelated_topic"
                    ),
                    "prompt": scripted["user"],
                    "answer": scripted["assistant"],
                    "parsed_answer": "",
                    "factual_answer": "",
                    "correct": "",
                    "included_in_later_context": True,
                })

            for check in checks_by_turn.get(
                completed_turn, pd.DataFrame()
            ).itertuples():
                sequence += 1
                rows.append({
                    "model": model_label,
                    "sequence": sequence,
                    "completed_turn": completed_turn,
                    "interaction_type": "original_claim_prompt_check",
                    "phase": (
                        "baseline"
                        if completed_turn == 0
                        else (
                            "misinformation"
                            if completed_turn <= len(induction)
                            else "unrelated_topic"
                        )
                    ),
                    "prompt": f"{check.question}\nAnswer only Yes or No.",
                    "answer": check.generated_response,
                    "parsed_answer": check.parsed_answer,
                    "factual_answer": check.factual_answer,
                    "correct": check.correct_probability,
                    "included_in_later_context": False,
                })

    transcript_path = output / "conversation_transcript.csv"
    pd.DataFrame(rows).to_csv(
        transcript_path, index=False, encoding="utf-8-sig"
    )
    return transcript_path


def behavioral_scores(bundle, original, turns, points, model_label):
    rows = []
    for turn in points:
        prefix = conversation_messages(turns, turn)
        correct_probabilities = []
        for item in original.itertuples():
            p_yes = yes_probability(bundle, prefix, item.question)
            correct_probability = p_yes if item.factual_answer == "Yes" else 1.0 - p_yes
            correct_probabilities.append(correct_probability)
            rows.append({
                "model": model_label,
                "turn": turn,
                "question_id": item.question_id,
                "question": item.question,
                "factual_answer": item.factual_answer,
                "correct_probability": correct_probability,
            })
        print(
            f"  {model_label}: behavior measured at turn {turn} "
            f"(mean correct probability {np.mean(correct_probabilities):.3f})",
            flush=True,
        )
    return pd.DataFrame(rows)


@torch.inference_mode()
def generate_yes_no_answer(bundle, prefix, question, max_new_tokens):
    """Ask the model directly and return its generated text plus parsed Yes/No answer."""
    messages = [dict(message) for message in prefix]
    messages.append({
        "role": "user",
        "content": f"{question}\nAnswer only Yes or No.",
    })
    rendered = bundle.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    encoded = bundle.tokenizer(
        rendered,
        return_tensors="pt",
        add_special_tokens=False,
    )
    device = next(bundle.model.parameters()).device
    encoded = {key: value.to(device) for key, value in encoded.items()}
    generated = bundle.model.generate(
        **encoded,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=(
            bundle.tokenizer.pad_token_id
            if bundle.tokenizer.pad_token_id is not None
            else bundle.tokenizer.eos_token_id
        ),
    )
    new_tokens = generated[0, encoded["input_ids"].shape[1]:]
    text = bundle.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    match = re.search(r"\b(yes|no)\b", text, flags=re.IGNORECASE)
    parsed_answer = match.group(1).capitalize() if match else None
    return text, parsed_answer


def prompted_behavioral_scores(
    bundle, original, turns, points, model_label, max_new_tokens
):
    """Measure reversion using actual generated answers at each checkpoint."""
    rows = []
    for turn in points:
        prefix = conversation_messages(turns, turn)
        checkpoint_scores = []
        for item in original.itertuples():
            response, parsed_answer = generate_yes_no_answer(
                bundle,
                prefix,
                str(item.question),
                max_new_tokens,
            )
            is_correct = (
                float(parsed_answer == item.factual_answer)
                if parsed_answer is not None
                else np.nan
            )
            checkpoint_scores.append(is_correct)
            rows.append({
                "model": model_label,
                "turn": turn,
                "question_id": item.question_id,
                "question": item.question,
                "factual_answer": item.factual_answer,
                "generated_response": response,
                "parsed_answer": parsed_answer,
                "correct_probability": is_correct,
            })
        mean_score = np.nanmean(checkpoint_scores)
        print(
            f"  {model_label}: direct prompts measured at turn {turn} "
            f"(mean correct response {mean_score:.3f})",
            flush=True,
        )
    return pd.DataFrame(rows)


def recovery_record(model, margin, behavior, switch_turn, probability_threshold):
    original_margin = margin[margin.question_set == "Original claim"].sort_values("turn")
    behavior_mean = behavior.groupby("turn", as_index=False).correct_probability.mean()
    combined = original_margin[["turn", "mean"]].merge(behavior_mean, on="turn")
    post_switch = combined[combined.turn > switch_turn]
    representation = post_switch[post_switch["mean"] >= 0]
    behavioral = post_switch[post_switch.correct_probability >= probability_threshold]
    both = post_switch[
        (post_switch["mean"] >= 0)
        & (post_switch.correct_probability >= probability_threshold)
    ]

    def first_and_delay(frame):
        if frame.empty:
            return None, None
        first = int(frame.iloc[0].turn)
        return first, first - switch_turn

    rep_turn, rep_delay = first_and_delay(representation)
    beh_turn, beh_delay = first_and_delay(behavioral)
    both_turn, both_delay = first_and_delay(both)
    return {
        "model": model,
        "topic_switch_turn": switch_turn,
        "representation_recovery_turn": rep_turn,
        "representation_turns_after_switch": rep_delay,
        "behavioral_recovery_turn": beh_turn,
        "behavioral_turns_after_switch": beh_delay,
        "joint_recovery_turn": both_turn,
        "joint_turns_after_switch": both_delay,
    }


def plot_results(
    margins, behavior, induction_end, total_turns, checkpoint_turns, output, check_method
):
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    colors = plt.cm.tab10(np.linspace(0, 1, margins.model.nunique()))

    for color, (model, model_margin) in zip(colors, margins.groupby("model", sort=False)):
        original = model_margin[model_margin.question_set == "Original claim"].sort_values("turn")
        generic = model_margin[model_margin.question_set == "Generic control"].sort_values("turn")
        axes[0].plot(
            original.turn, original["mean"], color=color, marker="o",
            linewidth=2, label=f"{model} - original claim",
        )
        axes[0].fill_between(
            original.turn, original.ci_low, original.ci_high, color=color, alpha=0.15,
        )
        axes[0].plot(
            generic.turn, generic["mean"], color=color, linestyle="--", alpha=0.65,
            label=f"{model} - generic control",
        )

        model_behavior = (
            behavior[behavior.model == model]
            .groupby("turn", as_index=False)
            .correct_probability.mean()
            .sort_values("turn")
        )
        axes[1].plot(
            model_behavior.turn,
            100 * model_behavior.correct_probability,
            color=color,
            marker="o",
            linewidth=2,
            label=model,
        )

    for ax in axes:
        ax.axvspan(0, induction_end, color="#f4a6a6", alpha=0.20)
        ax.axvspan(induction_end, total_turns, color="#9ecae1", alpha=0.22)
        ax.axvline(induction_end, color="#555555", linestyle=":", linewidth=1.5)
        ax.set_xticks(checkpoint_turns)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    axes[0].axhline(0, color="#888888", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Linear factuality margin")
    axes[0].set_title(
        "(a) Internal representation of the original claim",
        loc="left",
    )
    axes[0].legend(frameon=False, ncol=2, fontsize=8)

    axes[1].axhline(50, color="#888888", linestyle="--", linewidth=1)
    if check_method == "prompt_check":
        axes[1].set_ylabel("Generated answers correct (%)")
        axes[1].set_title(
            "(b) Accuracy of direct prompts about the original claim",
            loc="left",
        )
    else:
        axes[1].set_ylabel("Probability assigned to correct answer (%)")
        axes[1].set_title(
            "(b) Behavioral answer probability for the original claim",
            loc="left",
        )
    axes[1].set_xlabel("Completed conversation turns")
    axes[1].set_ylim(0, 100)
    axes[1].legend(frameon=False)

    fig.text(
        0.22, 0.955, "Misinformation induction", ha="center",
        color="#8c2d2d", fontsize=10,
    )
    fig.text(
        0.70, 0.955, "Unrelated-topic conversation", ha="center",
        color="#245b78", fontsize=10,
    )
    fig.text(
        0.5,
        0.01,
        "What this shows: the original fact is measured at baseline, while fabricated "
        "information is reinforced, and at the configured checkpoints after the conversation switches "
        "to an unrelated topic. The upper panel uses the same internal factuality probe "
        "for comparison; the lower panel uses "
        + (
            "actual generated Yes/No answers."
            if check_method == "prompt_check"
            else "Yes/No next-token probabilities."
        ),
        ha="center",
        fontsize=9,
        wrap=True,
    )
    fig.tight_layout(rect=(0, 0.075, 1, 0.94))
    fig.savefig(output / "topic_switch_reversion.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / "topic_switch_reversion.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=None,
        help="Optional override for how often the original claim is measured.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Optional output-subfolder name; defaults to the value in the config.",
    )
    parser.add_argument(
        "--check-method",
        choices=("probe_check", "prompt_check"),
        default=None,
        help="Use probability probes or actual generated Yes/No prompt responses.",
    )
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else HERE / args.config
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    active_models = [model for model in config["models"] if model.get("enabled", True)]
    if not active_models:
        raise ValueError("Enable at least one model in config.yaml.")

    generic = read_questions(resolve(config["data"]["generic_questions"]), {"train", "validation"})
    original = read_questions(resolve(config["data"]["original_questions"]), {"test"})
    phase_data = json.loads(
        resolve(config["data"]["phase_conversation"]).read_text(encoding="utf-8")
    )
    induction = phase_data["misinformation_turns"]
    topic_switch = phase_data["topic_switch_turns"]
    all_turns = induction + topic_switch
    interval = int(
        args.checkpoint_interval
        if args.checkpoint_interval is not None
        else config["experiment"]["checkpoint_interval"]
    )
    if interval < 1:
        raise ValueError("checkpoint_interval must be at least 1.")
    points = checkpoints(len(induction), len(topic_switch), interval)
    run_name = (
        args.run_name
        or config["experiment"].get("run_name")
        or f"every_{interval}_turns"
    )
    check_method = (
        args.check_method
        or config["experiment"].get("check_method", "probe_check")
    )
    result_root = (
        resolve(config["experiment"]["output_dir"])
        / "topic_switch_reversion"
        / check_method
    )
    output = output_folder(
        result_root,
        run_name,
        bool(config["experiment"].get("preserve_existing", True)),
    )
    transcript_path = write_conversation_transcript(induction, topic_switch, output)
    (output / "scripted_conversation_transcript.csv").write_bytes(
        transcript_path.read_bytes()
    )
    print(f"Conversation transcript saved to {transcript_path}", flush=True)

    all_scores, all_margins, all_behavior, recovery_rows = [], [], [], []
    model_metadata = []

    for model_spec in active_models:
        label = model_spec["label"]
        print(f"\nRunning {label}: {model_spec['name']}", flush=True)
        cfg = copy.deepcopy(config)
        cfg["_base"] = HERE
        cfg["model"] = {
            "name": model_spec["name"],
            "dtype": model_spec.get("dtype", "bfloat16"),
            "device_map": model_spec.get("device_map", "auto"),
        }
        bundle = load_model(cfg)
        full_prefix = conversation_messages(all_turns, len(all_turns))
        layer, probe, accuracies = fit_probe(bundle, cfg, generic, True, [full_prefix])
        prefixes = [
            (turn, conversation_messages(all_turns, turn))
            for turn in points
        ]
        scores = score_prefixes(
            bundle,
            cfg,
            probe,
            layer,
            [
                ("Original claim", original),
                ("Generic control", generic[generic.split == "validation"]),
            ],
            prefixes,
        )
        scores["model"] = label
        margins = margin_summary(scores, cfg)
        margins["model"] = label
        if check_method == "prompt_check":
            behavior = prompted_behavioral_scores(
                bundle,
                original,
                all_turns,
                points,
                label,
                int(config.get("prompt_check", {}).get("max_new_tokens", 8)),
            )
        else:
            behavior = behavioral_scores(
                bundle, original, all_turns, points, label
            )

        all_scores.append(scores)
        all_margins.append(margins)
        all_behavior.append(behavior)
        recovery_rows.append(
            recovery_record(
                label,
                margins,
                behavior,
                len(induction),
                float(config["recovery"]["correct_probability_threshold"]),
            )
        )
        model_metadata.append({
            "label": label,
            "model": model_spec["name"],
            "selected_layer_zero_based": layer,
            "validation_accuracies": accuracies,
        })
        del bundle
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    scores_frame = pd.concat(all_scores, ignore_index=True)
    margin_frame = pd.concat(all_margins, ignore_index=True)
    behavior_frame = pd.concat(all_behavior, ignore_index=True)
    recovery_frame = pd.DataFrame(recovery_rows)
    scores_frame.to_csv(output / "representation_scores.csv", index=False)
    margin_frame.to_csv(output / "margin_summary.csv", index=False)
    behavior_frame.to_csv(output / "behavior_scores.csv", index=False)
    if check_method == "prompt_check":
        behavior_frame.to_csv(output / "prompt_responses.csv", index=False)
        transcript_path = write_prompt_check_transcript(
            induction, topic_switch, behavior_frame, output
        )
        print(
            f"Combined prompt-check transcript saved to {transcript_path}",
            flush=True,
        )
    recovery_frame.to_csv(output / "recovery_summary.csv", index=False)
    plot_results(
        margin_frame,
        behavior_frame,
        len(induction),
        len(all_turns),
        points,
        output,
        check_method,
    )
    metadata = {
        "experiment": phase_data.get("experiment_name"),
        "run_name": run_name,
        "check_method": check_method,
        "output_folder": str(output),
        "checkpoint_interval": interval,
        "checkpoint_turns": points,
        "misinformation_turns": len(induction),
        "topic_switch_turns": len(topic_switch),
        "models": model_metadata,
        "interpretation": (
            "Positive factuality margin means correct and incorrect completions are ordered "
            "consistently with the trained probe. The lower panel uses "
            + (
                "actual generated Yes/No response accuracy."
                if check_method == "prompt_check"
                else "relative Yes/No next-token probability."
            )
        ),
    }
    (output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"\nDone. New experiment outputs saved to {output}", flush=True)


if __name__ == "__main__":
    main()
