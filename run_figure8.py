"""Run Figure 8: answer-wise factuality scores at every transformer layer."""
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from figure_common import json_input,prepare,questions
from run_experiment import OPPOSITE_DAY_TURNS,cached_activation,collect_examples,conversation_messages,fit_probe_for_layer,resolve
plt.switch_backend("Agg")
COLORS={("Generic","factual"):"#57b99d",("Context-relevant","factual"):"#3388c8",("Generic","nonfactual"):"#ef6548",("Context-relevant","nonfactual"):"#ad0040"}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure8/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); generic=questions(cfg,"generic_questions",{"train","validation"}); x,y=collect_examples(b,cfg,generic[generic.split=="train"],[[],OPPOSITE_DAY_TURNS]); panels=[]
    for title,ckey,qkey in (("(a) Consciousness","consciousness_conversation","consciousness_questions"),("(b) Chakras","chakras_conversation","chakras_questions")):
        c=json_input(cfg,ckey); target=questions(cfg,qkey,{"test"}); prefix=conversation_messages(c["turns"],len(c["turns"])); rows=[]
        valid_x,valid_y=collect_examples(b,cfg,generic[generic.split=="validation"],[[]])
        for layer in range(x.shape[1]):
            probe=fit_probe_for_layer(x,y,layer,cfg); acc=float((probe.predict(valid_x[:,layer])==valid_y).mean())
            for set_name,data in (("Generic",generic[generic.split=="validation"]),("Context-relevant",target)):
                for item in data.itertuples():
                    for answer in ("Yes","No"):
                        act=cached_activation(b,cfg,prefix,item.question,answer); rows.append({"layer":layer,"question_set":set_name,"answer_type":"factual" if answer==item.factual_answer else "nonfactual","score":float(probe.decision_function(act[layer:layer+1])[0]),"decodable":acc>=float(cfg["analysis"]["decodability_threshold"])})
        panels.append((title,pd.DataFrame(rows)))
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True); fig,axes=plt.subplots(1,2,figsize=(12,4.8))
    for ax,(title,data) in zip(axes,panels):
        data.to_csv(out/("consciousness_layer_scores.csv" if "Consciousness" in title else "chakras_layer_scores.csv"),index=False)
        s=data.groupby(["layer","question_set","answer_type","decodable"],as_index=False).score.mean()
        for keys,z in s.groupby(["question_set","answer_type"]):
            z=z.sort_values("layer"); ax.plot(z.layer,z.score,color=COLORS[keys],label=f"{keys[1]} ({'generic' if keys[0]=='Generic' else 'targeted'})"); bad=z[~z.decodable]; ax.plot(bad.layer,bad.score,color=COLORS[keys],alpha=.25)
        ax.axhline(0,color="#999",ls=(0,(3,3)),lw=.9); ax.set(title=title,xlabel="Model layer",ylabel="Factuality direction"); ax.legend(frameon=False,fontsize=8)
        for side in ("top","right"): ax.spines[side].set_visible(False)
    fig.text(.5,.01,"What this shows: answer projections at the final conversation turn across model depth. Faded segments mark layers where held-out generic factuality is not reliably decodable; stable ordering in later layers indicates the conversation effect is not confined to one selected layer.",ha="center",fontsize=9,wrap=True); fig.tight_layout(rect=(0,.11,1,1)); fig.savefig(out/"figure8.png",dpi=220,bbox_inches="tight"); fig.savefig(out/"figure8.pdf",bbox_inches="tight"); print(f"Figure 8 saved to {out}")
if __name__=="__main__": main()

