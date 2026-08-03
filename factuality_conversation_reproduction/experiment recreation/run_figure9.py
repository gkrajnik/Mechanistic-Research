"""Run Figure 9: Contrast-Consistent Search accuracy histograms."""
from pathlib import Path
import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from figure_common import json_input, prepare, questions
from run_experiment import cached_activation, conversation_messages, load_config, resolve

plt.switch_backend("Agg")


def pairs(bundle, cfg, data, prefix, layer):
    activations, labels = [], []
    for row in data.itertuples():
        yes = cached_activation(bundle, cfg, prefix, row.question, "Yes")[layer]
        no = cached_activation(bundle, cfg, prefix, row.question, "No")[layer]
        activations.append((yes, no))
        labels.extend([
            int(row.factual_answer == "Yes"),
            int(row.factual_answer == "No"),
        ])
    return np.asarray(activations), np.asarray(labels)


def train_ccs(x, steps):
    flat = x.reshape(-1, x.shape[-1])
    mean = flat.mean(0)
    std = flat.std(0) + 1e-6
    normalized = (x - mean) / std
    device = "cuda" if torch.cuda.is_available() else "cpu"
    normalized = torch.tensor(normalized, dtype=torch.float32, device=device)
    weight = torch.nn.Parameter(
        torch.randn(normalized.shape[-1], device=device) / np.sqrt(normalized.shape[-1])
    )
    bias = torch.nn.Parameter(torch.zeros((), device=device))
    optimizer = torch.optim.AdamW([weight, bias], lr=0.02)
    for _ in range(steps):
        probabilities = torch.sigmoid(normalized @ weight + bias)
        consistency = (probabilities[:, 0] - (1 - probabilities[:, 1])) ** 2
        confidence = torch.minimum(probabilities[:, 0], probabilities[:, 1]) ** 2
        loss = (consistency + confidence).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    return weight.detach().cpu().numpy(), float(bias.detach().cpu()), mean, std


def accuracy(model, x, labels, flip=False):
    weight, bias, mean, std = model
    prediction = (((x.reshape(-1, x.shape[-1]) - mean) / std) @ weight + bias > 0).astype(int)
    if flip:
        prediction = 1 - prediction
    return float((prediction == labels).mean())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("figures/figure9/config.yaml"))
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Skip model loading and require every activation to exist in the shared cache.",
    )
    args = parser.parse_args()

    if args.cache_only:
        cfg = load_config(args.config)
        bundle = None
        print("Cache-only mode: model weights will not be loaded.", flush=True)
    else:
        cfg, bundle = prepare(args.config)

    generic = questions(cfg, "generic_questions", {"train", "validation"})
    consciousness = questions(cfg, "consciousness_questions", {"test"})
    chakras = questions(cfg, "chakras_questions", {"test"})
    consciousness_chat = json_input(cfg, "consciousness_conversation")
    chakras_chat = json_input(cfg, "chakras_conversation")
    configured_layer = cfg["analysis"].get("layer")
    if configured_layer is None:
        first_question = generic[generic.split == "train"].iloc[0].question
        layer_count = cached_activation(
            bundle, cfg, [], first_question, "Yes"
        ).shape[0]
        layer = layer_count // 2
        print(
            f"Automatically selected middle layer {layer} "
            f"from {layer_count} transformer layers.",
            flush=True,
        )
    else:
        layer = int(configured_layer)

    train, _ = pairs(bundle, cfg, generic[generic.split == "train"], [], layer)
    conditions = [
        ("Generic Qs (empty)", *pairs(
            bundle, cfg, generic[generic.split == "validation"], [], layer
        )),
        ("Generic Qs (chakras)", *pairs(
            bundle, cfg, generic[generic.split == "validation"],
            conversation_messages(chakras_chat["turns"], len(chakras_chat["turns"])), layer
        )),
        ("Consciousness Qs (empty)", *pairs(bundle, cfg, consciousness, [], layer)),
        ("Consciousness Qs (consciousness)", *pairs(
            bundle, cfg, consciousness,
            conversation_messages(
                consciousness_chat["turns"], len(consciousness_chat["turns"])
            ), layer
        )),
        ("Chakras Qs (empty)", *pairs(bundle, cfg, chakras, [], layer)),
        ("Chakras Qs (chakras)", *pairs(
            bundle, cfg, chakras,
            conversation_messages(chakras_chat["turns"], len(chakras_chat["turns"])), layer
        )),
    ]

    rng = np.random.default_rng(int(cfg["experiment"]["seed"]))
    all_rows = []
    for run in range(int(cfg["analysis"]["runs"])):
        sample = train[rng.choice(len(train), len(train), replace=True)]
        model = train_ccs(sample, int(cfg["analysis"]["optimization_steps"]))
        base_x, base_y = conditions[0][1], conditions[0][2]
        raw_base = accuracy(model, base_x, base_y)
        flip = raw_base < 0.5
        oriented_base = max(raw_base, 1 - raw_base)
        for name, x, labels in conditions:
            all_rows.append({
                "run": run,
                "condition": name,
                "accuracy": accuracy(model, x, labels, flip),
                "generic_empty_accuracy": oriented_base,
            })

    all_frame = pd.DataFrame(all_rows)
    requested_threshold = float(cfg["analysis"]["keep_accuracy"])
    run_scores = all_frame.groupby("run")["generic_empty_accuracy"].first()
    retained_ids = run_scores[run_scores >= requested_threshold].index.tolist()
    selection_method = f"generic-empty accuracy >= {requested_threshold:.2f}"
    effective_threshold = requested_threshold

    if not retained_ids:
        if not bool(cfg["analysis"].get("allow_threshold_fallback", False)):
            raise RuntimeError(
                "No CCS runs met the configured retention threshold "
                f"{requested_threshold:.2f}. Best accuracy was {run_scores.max():.3f}. "
                "Lower analysis.keep_accuracy or enable analysis.allow_threshold_fallback."
            )
        fallback_count = min(
            int(cfg["analysis"].get("fallback_keep_runs", 20)),
            len(run_scores),
        )
        retained_ids = run_scores.nlargest(fallback_count).index.tolist()
        effective_threshold = float(run_scores.loc[retained_ids].min())
        selection_method = (
            f"fallback: top {fallback_count} runs "
            f"(effective minimum accuracy {effective_threshold:.3f})"
        )
        print(
            f"WARNING: no run met {requested_threshold:.2f}; using {selection_method}.",
            flush=True,
        )

    frame = all_frame[all_frame.run.isin(retained_ids)].copy()
    output = resolve(cfg["_base"], cfg["experiment"]["output_dir"])
    output.mkdir(parents=True, exist_ok=True)
    all_frame.to_csv(output / "ccs_all_runs.csv", index=False)
    frame.to_csv(output / "ccs_accuracies.csv", index=False)
    metadata = {
        "model": cfg["model"]["name"],
        "layer": layer,
        "requested_threshold": requested_threshold,
        "effective_threshold": effective_threshold,
        "selection_method": selection_method,
        "total_runs": int(run_scores.size),
        "retained_runs": int(len(retained_ids)),
        "best_generic_empty_accuracy": float(run_scores.max()),
        "cache_only": bool(args.cache_only),
    }
    (output / "selection_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    fig, axes = plt.subplots(3, 2, figsize=(10, 9), sharex=True, sharey=True)
    for ax, (name, _, _) in zip(axes.flat, conditions):
        values = frame.loc[frame.condition == name, "accuracy"]
        ax.hist(
            values,
            bins=np.linspace(0, 1, 11),
            color="#3388c8",
            edgecolor="white",
        )
        ax.axvline(0.5, color="#999999", linestyle="--")
        ax.set_title(name, fontsize=10)
        ax.set_ylabel("Count")
        ax.set_xlabel("Accuracy")

    fig.suptitle(f"CCS run selection: {selection_method}", fontsize=10)
    fig.text(
        0.5,
        0.01,
        "What this shows: the distribution of classification accuracy across retained "
        "unsupervised CCS runs. Values above 0.5 are better than chance; movement toward "
        "or below 0.5 after a conversation indicates that the discovered direction does "
        "not retain the same meaning in context.",
        ha="center",
        fontsize=9,
        wrap=True,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.97))
    fig.savefig(output / "figure9.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / "figure9.pdf", bbox_inches="tight")
    print(
        f"Figure 9 saved to {output}; retained {len(retained_ids)} runs.",
        flush=True,
    )


if __name__ == "__main__":
    main()
