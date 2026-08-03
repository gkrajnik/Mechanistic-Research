"""Run Figure 11: compare conversation effects across Gemma model sizes."""
from pathlib import Path
import argparse,gc
import matplotlib.pyplot as plt
import numpy as np
import torch
from figure_common import fit_probe,json_input,margin_summary,prepare,questions,score_prefixes
from run_experiment import conversation_messages,load_config,load_model,resolve
plt.switch_backend("Agg")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure11/config.yaml")); a=p.parse_args(); cfg=load_config(a.config); results=[]
    active_models=[item for item in cfg["models"] if item.get("enabled",True)]
    if not active_models: raise ValueError("Figure 11 requires at least one enabled model.")
    for item in active_models:
        cfg["model"]={"name":item["name"],"dtype":item.get("dtype","bfloat16"),"device_map":"auto"}; b=load_model(cfg); generic=questions(cfg,"generic_questions",{"train","validation"})
        for topic,ckey,qkey in (("Consciousness","consciousness_conversation","consciousness_questions"),("Chakras","chakras_conversation","chakras_questions")):
            c=json_input(cfg,ckey); target=questions(cfg,qkey,{"test"}); full=conversation_messages(c["turns"],len(c["turns"])); layer,probe,_=fit_probe(b,cfg,generic,True,[full]); prefixes=[(i,conversation_messages(c["turns"],i)) for i in range(len(c["turns"])+1)]; scores=score_prefixes(b,cfg,probe,layer,[("Generic",generic[generic.split=="validation"]),("Context-relevant",target)],prefixes); results.append((item["label"],topic,margin_summary(scores,cfg)))
        del b; gc.collect(); torch.cuda.empty_cache()
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True); fig,axes=plt.subplots(len(active_models),2,figsize=(12,4*len(active_models)),squeeze=False)
    colors={"Generic":"#57b99d","Context-relevant":"#3388c8"}
    for ax,(label,topic,s) in zip(axes.flat,results):
        for name,z in s.groupby("question_set"): z=z.sort_values("turn"); y=np.vstack([z["mean"]-z.ci_low,z.ci_high-z["mean"]]); ax.errorbar(z.turn,z["mean"],yerr=y,marker="o",color=colors[name],label=name)
        ax.axhline(0,color="#999",ls=(0,(3,3))); ax.set(title=f"{label} - {topic}",xlabel="Conversation turns",ylabel="Linear factuality margin"); ax.legend(frameon=False)
    fig.text(.5,.005,"What this shows: the same consciousness and chakras analyses across model scales. Comparing rows reveals whether larger models undergo stronger context-dependent changes; negative targeted margins indicate representational inversion.",ha="center",fontsize=9,wrap=True); fig.tight_layout(rect=(0,.05,1,1)); fig.savefig(out/"figure11.png",dpi=220,bbox_inches="tight"); fig.savefig(out/"figure11.pdf",bbox_inches="tight"); print(f"Figure 11 saved to {out}")
if __name__=="__main__": main()
