"""Advanced shared analyses for Figures 8, 9, and 13."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression

from run_experiment import ModelBundle, evaluation_messages, resolve


def _preanswer_cache_path(cfg: dict[str, Any], prefix: list[dict], question: str) -> Path:
    payload=json.dumps({"model":cfg["model"]["name"],"kind":"preanswer","prefix":prefix,"question":question},sort_keys=True).encode()
    cache=resolve(cfg["_base"],cfg["experiment"]["cache_dir"]); cache.mkdir(parents=True,exist_ok=True)
    return cache/f"{hashlib.sha256(payload).hexdigest()}.npz"


@torch.inference_mode()
def preanswer_all_layers(bundle: ModelBundle, cfg: dict[str, Any], prefix: list[dict], question: str) -> np.ndarray:
    path=_preanswer_cache_path(cfg,prefix,question)
    if path.exists(): return np.load(path)["activation"]
    messages=evaluation_messages(prefix,question)
    rendered=bundle.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    encoded=bundle.tokenizer(rendered,return_tensors="pt",add_special_tokens=False)
    device=next(bundle.model.parameters()).device; encoded={k:v.to(device) for k,v in encoded.items()}
    output=bundle.model(**encoded,output_hidden_states=True,use_cache=False,return_dict=True)
    result=np.stack([state[0,-1].float().cpu().numpy() for state in output.hidden_states[1:]])
    np.savez_compressed(path,activation=result); return result


def fit_behavior_probe(bundle: ModelBundle,cfg: dict[str,Any],generic: pd.DataFrame,prefixes:list[list[dict]]):
    train=generic[generic.split=="train"]; valid=generic[generic.split=="validation"]
    x=[]; y=[]
    for prefix in prefixes:
        for row in train.itertuples(): x.append(preanswer_all_layers(bundle,cfg,prefix,row.question)); y.append(int(row.factual_answer=="Yes"))
    x=np.stack(x); y=np.asarray(y); best=None
    forced=cfg["experiment"].get("layer"); layers=[int(forced)] if forced is not None else range(x.shape[1])
    for layer in layers:
        probe=LogisticRegression(C=float(cfg["probe"]["regularization_C"]),solver="lbfgs",max_iter=2000).fit(x[:,layer],y)
        vx=np.stack([preanswer_all_layers(bundle,cfg,[],r.question) for r in valid.itertuples()]); vy=np.asarray([int(r.factual_answer=="Yes") for r in valid.itertuples()]); acc=float((probe.predict(vx[:,layer])==vy).mean())
        if best is None or acc>best[0]: best=(acc,layer,probe)
    return best[1],best[2]


def decoder_layers(model: Any):
    candidates=[
        ("language_model","model","layers"), ("model","language_model","layers"),
        ("model","model","layers"), ("model","layers"),
    ]
    for path in candidates:
        obj=model
        try:
            for name in path: obj=getattr(obj,name)
            if len(obj): return obj
        except (AttributeError,TypeError): pass
    raise RuntimeError("Could not locate decoder layers for activation steering.")


def _answer_token_id(tokenizer: Any, answer: str) -> int:
    ids=tokenizer(" "+answer,add_special_tokens=False)["input_ids"]
    if not ids: ids=tokenizer(answer,add_special_tokens=False)["input_ids"]
    return ids[-1]


@torch.inference_mode()
def yes_probability(bundle:ModelBundle,prefix:list[dict],question:str,layer:int|None=None,direction:np.ndarray|None=None,strength:float=0.0)->float:
    messages=evaluation_messages(prefix,question)
    rendered=bundle.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    encoded=bundle.tokenizer(rendered,return_tensors="pt",add_special_tokens=False)
    device=next(bundle.model.parameters()).device; encoded={k:v.to(device) for k,v in encoded.items()}; handle=None
    if direction is not None and layer is not None and strength:
        def hook(_module,_inputs,output):
            hidden=output[0] if isinstance(output,tuple) else output
            vector=torch.as_tensor(direction,device=hidden.device,dtype=hidden.dtype); vector=vector/(vector.norm()+1e-12)
            changed=hidden.clone(); changed[:,-1,:]+=strength*vector
            return (changed,*output[1:]) if isinstance(output,tuple) else changed
        handle=decoder_layers(bundle.model)[layer].register_forward_hook(hook)
    try: logits=bundle.model(**encoded,use_cache=False,return_dict=True).logits[0,-1]
    finally:
        if handle is not None: handle.remove()
    yes,no=_answer_token_id(bundle.tokenizer,"Yes"),_answer_token_id(bundle.tokenizer,"No")
    pair=torch.softmax(torch.stack([logits[no],logits[yes]]).float(),dim=0)
    return float(pair[1].cpu())


def behavioral_bias(bundle:ModelBundle,dataset:pd.DataFrame,prefix:list[dict],layer:int|None=None,direction:np.ndarray|None=None,strength:float=0.0)->float:
    probabilities=[yes_probability(bundle,prefix,r.question,layer,direction,strength) for r in dataset.itertuples()]
    return 100.0*(2.0*np.mean(probabilities)-1.0)
