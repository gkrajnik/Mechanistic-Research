"""Evaluate frozen probes on held-out topics and wording without test-set tuning."""
from __future__ import annotations

import argparse, csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler

TARGETS=("factuality","roleplay")

def parse_args():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--config",type=Path,default=Path("config.yaml")); p.add_argument("--probe-run",type=Path); return p.parse_args()
def resolve(base,value):
    p=Path(value); return p if p.is_absolute() else (base/p).resolve()
def sha256(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def load_cfg(path):
    path=path.resolve(); cfg=yaml.safe_load(path.read_text(encoding="utf-8")); cfg["_base"]=path.parent; return cfg
def newest_matching(root,cfg):
    found=[]
    for d in root.glob("*"):
        p=d/"manifest.json"
        if not p.exists(): continue
        m=json.loads(p.read_text(encoding="utf-8"))
        if m.get("dataset_version")==cfg["dataset"]["version"] and m.get("model_name")==cfg["model"]["name"]: found.append(d)
    if not found: raise FileNotFoundError("No matching probe run")
    return max(found,key=lambda d:d.stat().st_mtime)
def load_probe(path): return {k:v for k,v in np.load(path).items()}
def label(meta,target):
    return np.array([int(r["factuality"]=="factual") if target=="factuality" else int(r["frame"]=="roleplay") for r in meta])
def margins(X,probe,layer):
    raw=X[:,layer,:]@probe["coefficient_raw"]+float(probe["intercept_raw"])
    return raw,(raw-float(probe["train_margin_mean"]))/float(probe["train_margin_std"])
def ba(y,p): return float(balanced_accuracy_score(y,p))
def metric_set(y,margin,threshold):
    pred=(margin>=threshold).astype(int); cm=confusion_matrix(y,pred,labels=[0,1])
    return {"n":int(len(y)),"accuracy":float(accuracy_score(y,pred)),"balanced_accuracy":ba(y,pred),"roc_auc":float(roc_auc_score(y,margin)),"tn":int(cm[0,0]),"fp":int(cm[0,1]),"fn":int(cm[1,0]),"tp":int(cm[1,1])}
def bootstrap_ci(y,margin,threshold,clusters,reps,seed):
    rng=np.random.default_rng(seed); unique=np.unique(clusters); vals=[]
    for _ in range(reps):
        sampled=rng.choice(unique,size=len(unique),replace=True); idx=np.concatenate([np.flatnonzero(clusters==c) for c in sampled])
        if len(np.unique(y[idx]))<2: continue
        vals.append((balanced_accuracy_score(y[idx],margin[idx]>=threshold),roc_auc_score(y[idx],margin[idx])))
    a=np.asarray(vals)
    return {"bootstrap_valid_repetitions":int(len(a)),"balanced_accuracy_ci_low":float(np.quantile(a[:,0],.025)),"balanced_accuracy_ci_high":float(np.quantile(a[:,0],.975)),"roc_auc_ci_low":float(np.quantile(a[:,1],.025)),"roc_auc_ci_high":float(np.quantile(a[:,1],.975))}
def subset_masks(meta):
    arr=lambda fn:np.array([fn(r) for r in meta])
    return {
      "heldout_topics":arr(lambda r:r["topic_split"]=="test" and r["template_partition"]=="development"),
      "heldout_wording":arr(lambda r:r["topic_split"]=="train" and r["template_partition"]=="heldout_wording"),
      "joint_generalization":arr(lambda r:r["topic_split"]=="test" and r["template_partition"]=="heldout_wording"),
      "validation_heldout_wording_descriptive":arr(lambda r:r["topic_split"]=="validation" and r["template_partition"]=="heldout_wording")}
def fit_layer_directions(X,meta,cfg):
    fit=np.array([r["topic_split"]=="train" and r["template_partition"]=="development" for r in meta]); result=[]
    for layer in range(X.shape[1]):
        dirs={}
        for target in TARGETS:
            scaler=StandardScaler().fit(X[fit,layer,:]); xs=scaler.transform(X[fit,layer,:]); y=label(meta,target)[fit]
            model=LogisticRegression(C=float(cfg["probe_training"]["regularization_C"]),solver="lbfgs",max_iter=int(cfg["probe_training"]["max_iterations"]),random_state=int(cfg["probe_training"]["random_seed"])).fit(xs,y)
            dirs[target]=model.coef_[0]/scaler.scale_
        cosine=float(np.dot(dirs["factuality"],dirs["roleplay"])/(np.linalg.norm(dirs["factuality"])*np.linalg.norm(dirs["roleplay"])))
        result.append({"layer":layer,"direction_cosine_similarity":cosine})
    return result
def main():
    args=parse_args(); cfg=load_cfg(args.config)
    probe_root=resolve(cfg["_base"],cfg["probe_training"]["output_dir"]); setting=cfg["probe_evaluation"]["probe_run"]
    probe_dir=resolve(cfg["_base"],args.probe_run) if args.probe_run else newest_matching(probe_root,cfg) if setting=="auto_latest" else resolve(cfg["_base"],setting)
    pm=json.loads((probe_dir/"manifest.json").read_text(encoding="utf-8")); layer=int(pm["selected_layer_zero_based"]); actdir=Path(pm["activation_run"])
    X=np.load(actdir/"activations.npz")["activations"]; meta=[json.loads(x) for x in (actdir/"metadata.jsonl").read_text(encoding="utf-8").splitlines() if x]
    probes={t:load_probe(probe_dir/f"{t}_probe.npz") for t in TARGETS}; allm={}; rawm={}
    for t in TARGETS: rawm[t],allm[t]=margins(X,probes[t],layer)
    masks=subset_masks(meta); rows=[]; reps=int(cfg["probe_evaluation"]["bootstrap_repetitions"]); seed=int(cfg["probe_evaluation"]["bootstrap_seed"])
    for subset,mask in masks.items():
        clusters=np.array([r["pair_id"] for r in meta])[mask]
        for target in TARGETS:
            y=label(meta,target)[mask]; threshold=float(probes[target]["standardized_zero_threshold"]); base=metric_set(y,allm[target][mask],threshold); ci=bootstrap_ci(y,allm[target][mask],threshold,clusters,reps,seed)
            rows.append({"subset":subset,"target":target,"subgroup":"overall",**base,**ci})
            group_field="frame" if target=="factuality" else "factuality"
            for group in sorted({r[group_field] for r,m in zip(meta,mask) if m}):
                sub=mask & np.array([r[group_field]==group for r in meta]); sy=label(meta,target)[sub]
                rows.append({"subset":subset,"target":target,"subgroup":f"{group_field}={group}",**metric_set(sy,allm[target][sub],threshold),"bootstrap_valid_repetitions":"","balanced_accuracy_ci_low":"","balanced_accuracy_ci_high":"","roc_auc_ci_low":"","roc_auc_ci_high":""})
    cosines=fit_layer_directions(X,meta,cfg)
    # Control analysis: training-only logistic models using target margin alone, nuisance margin alone, or both.
    fit=np.array([r["topic_split"]=="train" and r["template_partition"]=="development" for r in meta]); controls=[]
    for target in TARGETS:
        nuisance="roleplay" if target=="factuality" else "factuality"; y=label(meta,target)
        features={"target_margin_only":allm[target][:,None],"nuisance_margin_only":allm[nuisance][:,None],"both_margins":np.column_stack([allm[target],allm[nuisance]])}
        models={name:LogisticRegression(C=1.0,solver="lbfgs",max_iter=2000,random_state=int(cfg["probe_training"]["random_seed"])).fit(v[fit],y[fit]) for name,v in features.items()}
        for subset,mask in masks.items():
            for name,model in models.items(): controls.append({"target":target,"subset":subset,"control_model":name,"balanced_accuracy":ba(y[mask],model.predict(features[name][mask])),"target_margin_coefficient":float(model.coef_[0][0]) if name!="nuisance_margin_only" else "","nuisance_margin_coefficient":float(model.coef_[0][-1]) if name!="target_margin_only" else ""})
    timestamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); out=resolve(cfg["_base"],cfg["probe_evaluation"]["output_dir"])/f"{cfg['dataset']['version']}_{cfg['model']['name'].replace('/','__')}_{timestamp}"; out.mkdir(parents=True)
    for name,data in (("evaluation_metrics.csv",rows),("direction_cosines.csv",cosines),("controlled_margin_metrics.csv",controls)):
        with (out/name).open("w",encoding="utf-8",newline="") as h: w=csv.DictWriter(h,fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
    manifest={"created_utc":timestamp,"dataset_version":cfg["dataset"]["version"],"model_name":cfg["model"]["name"],"probe_run":str(probe_dir),"selected_layer_zero_based":layer,"probe_manifest_sha256":sha256(probe_dir/"manifest.json"),"bootstrap_method":"pair_id cluster bootstrap","bootstrap_repetitions":reps,"subsets":{k:int(v.sum()) for k,v in masks.items()},"test_tuning_performed":False}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8"); print(f"Saved locked Stage 7 evaluation to {out}")
if __name__=="__main__": main()
