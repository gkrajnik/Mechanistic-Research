"""Train independent factuality and role-play probes and select one shared layer.

Fitting uses train topics with development wording. Layer selection uses validation topics with
development wording. No test-topic or held-out-wording row is scored in this stage.
"""
from __future__ import annotations

import argparse, csv, hashlib, json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.preprocessing import StandardScaler

@dataclass
class FittedProbe:
    scaler: StandardScaler
    model: LogisticRegression
    train_margin_mean: float
    train_margin_std: float

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--activation-run", type=Path)
    return parser.parse_args()

def resolve(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def load_config(path: Path) -> dict[str, Any]:
    path = path.resolve()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")); cfg["_base"] = path.parent
    for section, key in (("model","name"),("dataset","version"),("probe_training","activation_run")):
        if not cfg.get(section, {}).get(key): raise ValueError(f"config.yaml must define {section}.{key}")
    return cfg

def find_activation_run(cfg: dict[str, Any], override: Path | None) -> Path:
    if override:
        candidate = resolve(cfg["_base"], override)
    elif str(cfg["probe_training"]["activation_run"]) != "auto_latest_full":
        candidate = resolve(cfg["_base"], cfg["probe_training"]["activation_run"])
    else:
        root = resolve(cfg["_base"], cfg["activation_extraction"]["output_dir"]); candidates = []
        for directory in root.glob("*"):
            manifest_path = directory / "manifest.json"
            if not directory.is_dir() or not manifest_path.exists(): continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (manifest.get("mode") == "full" and
                manifest.get("dataset_version") == cfg["dataset"]["version"] and
                manifest.get("model_name") == cfg["model"]["name"]): candidates.append(directory)
        if not candidates: raise FileNotFoundError("No matching full activation run was found")
        candidate = max(candidates, key=lambda item: item.stat().st_mtime)
    for required in ("activations.npz","metadata.jsonl","manifest.json"):
        if not (candidate / required).exists(): raise FileNotFoundError(f"Missing {required}: {candidate}")
    return candidate

def load_inputs(run_dir: Path) -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    activations = np.load(run_dir / "activations.npz")["activations"]
    metadata = [json.loads(line) for line in (run_dir/"metadata.jsonl").read_text(encoding="utf-8").splitlines() if line]
    manifest = json.loads((run_dir/"manifest.json").read_text(encoding="utf-8"))
    if activations.ndim != 3 or activations.shape[0] != len(metadata): raise ValueError("Activation/metadata mismatch")
    if manifest.get("example_count") != len(metadata) or manifest.get("mode") != "full": raise ValueError("Not a complete full run")
    if not np.isfinite(activations).all(): raise ValueError("Activations contain NaN or infinity")
    return activations, metadata, manifest

def mask_for(metadata: list[dict[str, Any]], split: str, partition: str) -> np.ndarray:
    return np.asarray([r["topic_split"] == split and r["template_partition"] == partition for r in metadata])

def labels(metadata: list[dict[str, Any]], target: str) -> np.ndarray:
    if target == "factuality": return np.asarray([int(r["factuality"] == "factual") for r in metadata])
    if target == "roleplay": return np.asarray([int(r["frame"] == "roleplay") for r in metadata])
    raise ValueError(target)

def fit_probe(x: np.ndarray, y: np.ndarray, cfg: dict[str, Any]) -> FittedProbe:
    scaler = StandardScaler().fit(x); scaled = scaler.transform(x)
    model = LogisticRegression(C=float(cfg["probe_training"]["regularization_C"]), solver="lbfgs",
        max_iter=int(cfg["probe_training"]["max_iterations"]),
        random_state=int(cfg["probe_training"]["random_seed"])).fit(scaled, y)
    margins = model.decision_function(scaled); std = float(np.std(margins))
    if not np.isfinite(std) or std <= 0: raise RuntimeError("Invalid training-margin standard deviation")
    return FittedProbe(scaler, model, float(np.mean(margins)), std)

def score(probe: FittedProbe, x: np.ndarray, y: np.ndarray) -> dict[str,float]:
    pred = probe.model.predict(probe.scaler.transform(x))
    return {"accuracy":float(accuracy_score(y,pred)),"balanced_accuracy":float(balanced_accuracy_score(y,pred))}

def save_probe(path: Path, probe: FittedProbe, layer: int, target: str) -> None:
    coef_scaled = probe.model.coef_[0].astype(np.float64); intercept_scaled = float(probe.model.intercept_[0])
    coef_raw = coef_scaled / probe.scaler.scale_
    intercept_raw = intercept_scaled - float(np.dot(coef_scaled, probe.scaler.mean_/probe.scaler.scale_))
    np.savez_compressed(path, target=np.asarray(target), layer=np.asarray(layer),
        positive_class=np.asarray("factual" if target=="factuality" else "roleplay"),
        scaler_mean=probe.scaler.mean_, scaler_scale=probe.scaler.scale_,
        coefficient_scaled=coef_scaled, intercept_scaled=np.asarray(intercept_scaled),
        coefficient_raw=coef_raw, intercept_raw=np.asarray(intercept_raw),
        train_margin_mean=np.asarray(probe.train_margin_mean), train_margin_std=np.asarray(probe.train_margin_std),
        standardized_zero_threshold=np.asarray(-probe.train_margin_mean/probe.train_margin_std))

def main() -> None:
    args=parse_args(); cfg=load_config(args.config); run_dir=find_activation_run(cfg,args.activation_run)
    activations,metadata,activation_manifest=load_inputs(run_dir)
    fit_mask=mask_for(metadata,"train","development"); val_mask=mask_for(metadata,"validation","development")
    if (int(fit_mask.sum()),int(val_mask.sum())) != (240,80): raise ValueError(f"Unexpected fit/validation counts: {fit_mask.sum()}/{val_mask.sum()}")
    targets=("factuality","roleplay"); y={target:labels(metadata,target) for target in targets}
    records=[]; fitted_by_layer={}
    for layer in range(activations.shape[1]):
        fitted_by_layer[layer]={}; row={"layer":layer}; val_scores=[]
        for target in targets:
            probe=fit_probe(activations[fit_mask,layer,:],y[target][fit_mask],cfg); fitted_by_layer[layer][target]=probe
            train=score(probe,activations[fit_mask,layer,:],y[target][fit_mask]); val=score(probe,activations[val_mask,layer,:],y[target][val_mask])
            for metric,value in train.items(): row[f"{target}_train_{metric}"]=value
            for metric,value in val.items(): row[f"{target}_validation_{metric}"]=value
            row[f"{target}_iterations"]=int(probe.model.n_iter_[0]); val_scores.append(val["balanced_accuracy"])
        row["mean_validation_balanced_accuracy"]=float(np.mean(val_scores)); records.append(row)
        print(f"Layer {layer:02d}: factuality={val_scores[0]:.3f}, roleplay={val_scores[1]:.3f}, mean={row['mean_validation_balanced_accuracy']:.3f}")
    selected_layer=max(range(len(records)),key=lambda layer:(records[layer]["mean_validation_balanced_accuracy"],-layer))
    timestamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output=resolve(cfg["_base"],cfg["probe_training"]["output_dir"])/f"{cfg['dataset']['version']}_{cfg['model']['name'].replace('/','__')}_{timestamp}"
    output.mkdir(parents=True,exist_ok=False)
    with (output/"layer_metrics.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    for target in targets: save_probe(output/f"{target}_probe.npz",fitted_by_layer[selected_layer][target],selected_layer,target)
    selected={"selected_layer_zero_based":selected_layer,
        "selection_rule":"maximum mean validation balanced accuracy across factuality and roleplay; earliest layer breaks ties",
        "factuality_validation_balanced_accuracy":records[selected_layer]["factuality_validation_balanced_accuracy"],
        "roleplay_validation_balanced_accuracy":records[selected_layer]["roleplay_validation_balanced_accuracy"],
        "mean_validation_balanced_accuracy":records[selected_layer]["mean_validation_balanced_accuracy"]}
    (output/"selected_layer.json").write_text(json.dumps(selected,indent=2)+"\n",encoding="utf-8")
    manifest={"created_utc":timestamp,"dataset_version":cfg["dataset"]["version"],"model_name":cfg["model"]["name"],
        "model_revision":activation_manifest.get("model_revision"),"activation_run":str(run_dir),"activation_shape":list(activations.shape),
        "activation_sha256":sha256(run_dir/"activations.npz"),"metadata_sha256":sha256(run_dir/"metadata.jsonl"),
        "fit_subset":{"topic_split":"train","template_partition":"development","rows":int(fit_mask.sum())},
        "selection_subset":{"topic_split":"validation","template_partition":"development","rows":int(val_mask.sum())},
        "test_rows_used":0,"heldout_wording_rows_used":0,"feature_standardization":"per-layer StandardScaler fitted on fit subset only",
        "margin_standardization":"training decision-function mean and population standard deviation",
        "regularization_C":float(cfg["probe_training"]["regularization_C"]),**selected}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"Selected shared layer {selected_layer}; saved Stage 6 outputs to {output}")

if __name__ == "__main__": main()
