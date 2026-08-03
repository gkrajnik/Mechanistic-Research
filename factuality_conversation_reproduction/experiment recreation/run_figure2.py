"""Run Figure 2: opposite-day factuality projections/margin and ethics margin."""
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import numpy as np
from figure_common import fit_probe, margin_summary, prepare, questions, score_prefixes
from plot_figure7 import summarize_scores
from run_experiment import OPPOSITE_DAY_TURNS, resolve

plt.switch_backend("Agg")

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure2/config.yaml")); a=p.parse_args()
    cfg,bundle=prepare(a.config); panels=[]; saved=[]
    prefixes=[(i, OPPOSITE_DAY_TURNS[:2*i]) for i in range(4)]
    for concept,key in (("Factuality","generic_questions"),("Ethics","ethics_questions")):
        data=questions(cfg,key,{"train","validation"}); layer,probe,_=fit_probe(bundle,cfg,data,False)
        scores=score_prefixes(bundle,cfg,probe,layer,[("Generic",data[data.split=="validation"])],prefixes)
        saved.append((concept,scores)); panels.append((concept,margin_summary(scores,cfg)))
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True)
    for name,s in saved: s.to_csv(out/f"{name.lower()}_scores.csv",index=False)
    fig,axes=plt.subplots(1,3,figsize=(15,4.3))
    fact_summary=summarize_scores(saved[0][1],int(cfg["statistics"]["bootstrap_samples"]),float(cfg["statistics"]["confidence"]),int(cfg["experiment"]["seed"]))
    for kind,color in (("factual","#57b99d"),("nonfactual","#ef6548")):
        z=fact_summary[fact_summary.answer_type==kind].sort_values("turn"); y=np.vstack([z["mean"]-z.ci_low,z.ci_high-z["mean"]]); axes[0].errorbar(z.turn,z["mean"],yerr=y,marker="o",color=color,label=f"{kind} (generic)")
    for ax,(title,summary) in zip(axes[1:],panels):
        z=summary.sort_values("turn"); y=np.vstack([z["mean"]-z.ci_low,z.ci_high-z["mean"]]); ax.errorbar(z.turn,z["mean"],yerr=y,marker="o",color="#3388c8")
        ax.set_ylabel(f'Linear "{title.lower()}" margin')
    axes[0].set_ylabel('"Factuality" direction'); axes[0].legend(frameon=False)
    for ax in axes:
        ax.axhline(0,color="#999",ls=(0,(3,3)),lw=.9); ax.set_xlabel("Conversation turns")
        for side in ("top","right"): ax.spines[side].set_visible(False)
    fig.text(.5,.01,"What this shows: whether factual and ethical Yes/No completions remain aligned with linear probe directions as the opposite-day instruction and examples accumulate. Negative margins mean the probe ordering has reversed relative to ground truth.",ha="center",va="bottom",fontsize=9,wrap=True)
    fig.tight_layout(rect=(0,.12,1,1)); fig.savefig(out/"figure2.png",dpi=220,bbox_inches="tight"); fig.savefig(out/"figure2.pdf",bbox_inches="tight")
    print(f"Figure 2 saved to {out}")
if __name__=="__main__": main()
