"""Extract forced-answer activations for the validated role-play/factuality dataset.

The default run is deliberately a small smoke test. It loads one centrally configured model,
selects eight balanced examples, extracts every transformer layer at the final forced-answer
token, and writes a resumable cache plus metadata. Pass --full only after inspecting the smoke test.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml


@dataclass
class ModelBundle:
    tokenizer: Any
    model: Any
    resolved_revision: str | None
    runtime_device: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="Process the complete frozen dataset.")
    mode.add_argument("--limit", type=int, help="Process a balanced subset of this many rows.")
    parser.add_argument("--cache-only", action="store_true", help="Never load a model; require cached rows.")
    parser.add_argument("--ignore-cache", action="store_true", help="Recompute selected rows without deleting old cache files.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and show the selected rows only.")
    parser.add_argument("--allow-cpu-full", action="store_true", help="Permit --full even when the model is on CPU.")
    return parser.parse_args()


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def load_settings(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    cfg["_base"] = config_path.parent
    if not cfg.get("model", {}).get("name"):
        raise ValueError("config.yaml must define model.name")
    if cfg.get("dataset", {}).get("version") != "pilot_v1":
        raise ValueError("Stage 5 currently requires the frozen pilot_v1 dataset")
    return cfg


def read_dataset(cfg: dict[str, Any]) -> list[dict[str, str]]:
    path = resolve(cfg["_base"], cfg["dataset"]["path"])
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "example_id", "pair_id", "topic_split", "template_partition", "frame", "factuality",
        "context", "question", "forced_answer", "factual_answer", "review_status",
    }
    if not rows or (missing := required.difference(rows[0])):
        raise ValueError(f"{path} is empty or missing columns: {sorted(missing)}")
    if len(rows) != 480:
        raise ValueError(f"pilot_v1 must contain 480 rows; found {len(rows)}")
    if any(row["review_status"] != "validated_pilot_v1" for row in rows):
        raise ValueError("Every input row must have review_status=validated_pilot_v1")
    if any(row["forced_answer"] not in {"Yes", "No"} for row in rows):
        raise ValueError("forced_answer values must be exactly Yes or No")
    if len({row["example_id"] for row in rows}) != len(rows):
        raise ValueError("example_id values must be unique")
    return rows


def balanced_subset(rows: list[dict[str, str]], count: int, seed: int) -> list[dict[str, str]]:
    if count <= 0 or count > len(rows):
        raise ValueError(f"limit must be between 1 and {len(rows)}")
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault((row["frame"], row["factuality"]), []).append(row)
    rng = random.Random(seed)
    for group_rows in groups.values():
        group_rows.sort(key=lambda row: row["example_id"])
        rng.shuffle(group_rows)
    selected: list[dict[str, str]] = []
    keys = sorted(groups)
    while len(selected) < count:
        made_progress = False
        for key in keys:
            if groups[key] and len(selected) < count:
                selected.append(groups[key].pop())
                made_progress = True
        if not made_progress:
            break
    return sorted(selected, key=lambda row: row["example_id"])


def torch_dtype(name: str) -> Any:
    import torch
    if not hasattr(torch, name):
        raise ValueError(f"Unknown torch dtype {name!r}")
    value = getattr(torch, name)
    if not isinstance(value, torch.dtype):
        raise ValueError(f"torch.{name} is not a dtype")
    return value


def load_model(cfg: dict[str, Any]) -> ModelBundle:
    import transformers
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    model_cfg = cfg["model"]
    name = model_cfg["name"]
    print(f"Loading tokenizer and model: {name}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(name, use_fast=True)
    architecture = AutoConfig.from_pretrained(name)
    options = {
        "torch_dtype": torch_dtype(model_cfg.get("dtype", "bfloat16")),
        "device_map": model_cfg.get("device_map", "auto"),
        "low_cpu_mem_usage": True,
    }
    if architecture.model_type == "gemma3":
        cls = getattr(transformers, "Gemma3ForConditionalGeneration", None)
        if cls is None:
            raise RuntimeError("Gemma 3 multimodal loading requires transformers>=4.51")
    elif architecture.model_type == "gemma3_text":
        cls = getattr(transformers, "Gemma3ForCausalLM", AutoModelForCausalLM)
    else:
        cls = AutoModelForCausalLM
    model = cls.from_pretrained(name, **options)
    model.eval()
    revision = getattr(model.config, "_commit_hash", None)
    runtime_device = str(next(model.parameters()).device)
    print(f"Model runtime device: {runtime_device}", flush=True)
    return ModelBundle(tokenizer=tokenizer, model=model, resolved_revision=revision, runtime_device=runtime_device)


def render_example(tokenizer: Any, row: dict[str, str]) -> tuple[str, dict[str, Any], int]:
    messages = [
        {"role": "user", "content": f"{row['context'].strip()}\n\n{row['question'].strip()}\nAnswer only Yes or No."},
        {"role": "assistant", "content": row["forced_answer"]},
    ]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    encoded = tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
    ids = encoded["input_ids"][0].tolist()
    candidates = []
    for text in (row["forced_answer"], " " + row["forced_answer"], "\n" + row["forced_answer"]):
        token_ids = tokenizer(text, add_special_tokens=False)["input_ids"]
        if token_ids:
            candidates.append(token_ids)
    matches: list[tuple[int, int]] = []
    for candidate in candidates:
        for start in range(len(ids) - len(candidate) + 1):
            if ids[start:start + len(candidate)] == candidate:
                matches.append((start, len(candidate)))
    if not matches:
        raise RuntimeError(f"Could not locate forced answer token for {row['example_id']}")
    start, width = max(matches)
    return rendered, encoded, start + width - 1


def cache_key(cfg: dict[str, Any], row: dict[str, str], rendered: str) -> str:
    payload = {
        "model": cfg["model"]["name"], "dataset_version": cfg["dataset"]["version"],
        "layers": "all_transformer_blocks", "answer_position": "final_token_of_forced_answer",
        "example_id": row["example_id"], "prompt": rendered, "answer": row["forced_answer"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def extract_one(
    bundle: ModelBundle, encoded: dict[str, Any], answer_position: int, max_length: int
) -> np.ndarray:
    import torch
    if encoded["input_ids"].shape[1] > max_length:
        raise ValueError(f"Prompt exceeds the configured {max_length}-token safety limit")
    device = next(bundle.model.parameters()).device
    encoded = {name: tensor.to(device) for name, tensor in encoded.items()}
    with torch.inference_mode():
        output = bundle.model(**encoded, output_hidden_states=True, use_cache=False, return_dict=True)
    if not output.hidden_states or len(output.hidden_states) < 2:
        raise RuntimeError("Model did not return per-layer hidden states")
    return np.stack([state[0, answer_position].float().cpu().numpy() for state in output.hidden_states[1:]])


def main() -> None:
    args = parse_args()
    cfg = load_settings(args.config)
    rows = read_dataset(cfg)
    extraction = cfg["activation_extraction"]
    limit = len(rows) if args.full else args.limit or int(extraction["smoke_test_rows"])
    selected = rows if limit == len(rows) else balanced_subset(rows, limit, int(extraction["seed"]))
    print(f"Validated dataset: {len(rows)} rows; selected for this run: {len(selected)}")
    for row in selected:
        print(f"  {row['example_id']}: {row['frame']}/{row['factuality']} -> {row['forced_answer']}")
    if args.dry_run:
        print("Dry run complete; no model was loaded.")
        return

    bundle = None if args.cache_only else load_model(cfg)
    if (
        args.full and bundle is not None and bundle.runtime_device.startswith("cpu")
        and bool(extraction.get("require_cuda_for_full", True)) and not args.allow_cpu_full
    ):
        raise RuntimeError(
            "Full extraction was stopped because the model loaded on CPU. Install a CUDA-enabled "
            "PyTorch build, or rerun with --allow-cpu-full only if the long CPU run is intentional."
        )
    if args.cache_only:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["name"], use_fast=True, local_files_only=True)
    else:
        tokenizer = bundle.tokenizer
    cache_dir = resolve(cfg["_base"], extraction["cache_dir"]) / cfg["dataset"]["version"] / cfg["model"]["name"].replace("/", "__")
    cache_dir.mkdir(parents=True, exist_ok=True)
    activations, metadata = [], []
    for index, row in enumerate(selected, start=1):
        rendered, encoded, answer_position = render_example(tokenizer, row)
        key = cache_key(cfg, row, rendered)
        cache_path = cache_dir / f"{key}.npz"
        if cache_path.exists() and not args.ignore_cache:
            activation = np.load(cache_path)["activation"]
            source = "cache"
        else:
            if bundle is None:
                raise RuntimeError(f"Missing cached activation for {row['example_id']}")
            print(f"[{index}/{len(selected)}] Extracting {row['example_id']}", flush=True)
            activation = extract_one(bundle, encoded, answer_position, int(extraction["max_length"]))
            np.savez_compressed(cache_path, activation=activation.astype(np.float32))
            source = "model"
        activations.append(activation.astype(np.float32))
        metadata.append({
            **row, "row_index": index - 1, "cache_key": key, "cache_source": source,
            "token_count": int(encoded["input_ids"].shape[1]), "answer_token_position": answer_position,
            "layer_count": int(activation.shape[0]), "hidden_size": int(activation.shape[1]),
        })
    stacked = np.stack(activations)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mode = "full" if args.full else f"smoke_{len(selected)}"
    run_dir = resolve(cfg["_base"], extraction["output_dir"]) / f"{cfg['dataset']['version']}_{mode}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(run_dir / "activations.npz", activations=stacked)
    with (run_dir / "metadata.jsonl").open("w", encoding="utf-8") as handle:
        for item in metadata:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    import torch
    import transformers
    manifest = {
        "created_utc": timestamp, "dataset_version": cfg["dataset"]["version"],
        "model_name": cfg["model"]["name"], "model_revision": bundle.resolved_revision if bundle else None,
        "runtime_device": bundle.runtime_device if bundle else "cache-only",
        "mode": mode, "example_count": len(selected), "activation_shape": list(stacked.shape),
        "answer_position": extraction["answer_position"], "saved_dtype": str(stacked.dtype),
        "transformers_version": transformers.__version__, "torch_version": torch.__version__,
        "numpy_version": np.__version__, "python_version": platform.python_version(),
        "config_path": str(args.config.resolve()), "command": " ".join(sys.argv),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Saved activation shape {stacked.shape} to {run_dir}")


if __name__ == "__main__":
    main()
