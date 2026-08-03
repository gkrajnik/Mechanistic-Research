"""Run Figure 12: Qwen3 opposite-day factuality and ethics margins."""
from pathlib import Path
import argparse
from figure_common import fit_probe,margin_summary,plot_margin_panels,prepare,questions,score_prefixes
from run_experiment import OPPOSITE_DAY_TURNS,resolve
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure12/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); prefixes=[(i,OPPOSITE_DAY_TURNS[:2*i]) for i in range(4)]; panels=[]
    for title,key in ((('(a) "Factuality" margin'),'generic_questions'),(('(b) "Ethics" margin'),'ethics_questions')):
        data=questions(cfg,key,{"train","validation"}); layer,probe,_=fit_probe(b,cfg,data,False); scores=score_prefixes(b,cfg,probe,layer,[("Generic",data[data.split=="validation"])],prefixes); panels.append((title,margin_summary(scores,cfg)))
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); plot_margin_panels(panels,out/"figure12.png",y_label="Linear probe margin",caption="What this shows: whether Qwen3's factuality and ethics probe margins reverse as opposite-day instructions and examples accumulate. A move below zero means the learned direction ranks incorrect completions above correct ones."); print(f"Figure 12 saved to {out}")
if __name__=="__main__": main()

