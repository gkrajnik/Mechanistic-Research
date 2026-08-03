"""Run Figure 13: causal steering before Yes/No answers in two contexts."""
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import pandas as pd
from advanced_common import behavioral_bias,fit_behavior_probe
from figure_common import json_input,prepare,questions
from run_experiment import OPPOSITE_DAY_TURNS,conversation_messages,resolve
plt.switch_backend("Agg")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure13/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); generic=questions(cfg,"generic_questions",{"train","validation"}); layer,probe=fit_behavior_probe(b,cfg,generic,[[],OPPOSITE_DAY_TURNS]); direction=probe.coef_[0]; strength=float(cfg["steering"]["strength"]); rows=[]
    specs=[("Consciousness","consciousness_questions","consciousness_conversation"),("Chakras","chakras_questions","chakras_conversation")]
    for topic,qkey,ckey in specs:
        data=questions(cfg,qkey,{"test"}); c=json_input(cfg,ckey); contexts=[("Empty context",[]),(f"{topic} conversation",conversation_messages(c["turns"],len(c["turns"])))]
        for name,prefix in contexts:
            before=behavioral_bias(b,data,prefix); after=behavioral_bias(b,data,prefix,layer,direction,strength); rows.append({"topic":topic,"context":name,"before":before,"after":after})
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True); frame=pd.DataFrame(rows); frame.to_csv(out/"steering_bias.csv",index=False); fig,axes=plt.subplots(1,2,figsize=(11,4.8))
    for ax,(topic,z) in zip(axes,frame.groupby("topic",sort=False)):
        for i,row in enumerate(z.itertuples()): ax.annotate("",xy=(i,row.after),xytext=(i,row.before),arrowprops=dict(arrowstyle="->",lw=2,color="#3388c8" if i==0 else "#ad0040")); ax.scatter([i],[row.before],color="#555",zorder=3)
        ax.axhline(0,color="#999",ls="--"); ax.set_xticks(range(len(z)),z.context); ax.set_ylim(-105,105); ax.set_yticks([-100,-50,0,50,100],["100% No","75% No","Balanced","75% Yes","100% Yes"]); ax.set_title(topic); ax.set_ylabel("Behavioral Yes/No bias")
    fig.text(.5,.01,"What this shows: each arrow starts at the model's unsteered Yes/No bias and ends after adding the learned behavioral-factuality direction before the answer. Arrows can point differently in empty and conversation contexts, showing that the same intervention may have context-dependent causal effects.",ha="center",fontsize=9,wrap=True); fig.tight_layout(rect=(0,.12,1,1)); fig.savefig(out/"figure13.png",dpi=220,bbox_inches="tight"); fig.savefig(out/"figure13.pdf",bbox_inches="tight"); print(f"Figure 13 saved to {out}")
if __name__=="__main__": main()
