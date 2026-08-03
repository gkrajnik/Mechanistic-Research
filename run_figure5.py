"""Run Figure 5: score after every message (ply) in a two-sided argument."""
from pathlib import Path
import argparse
from figure_common import fit_probe,json_input,margin_summary,plot_margin_panels,prepare,questions,score_prefixes
from run_experiment import resolve
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure5/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); c=json_input(cfg,"argument"); messages=c["messages"]; generic=questions(cfg,"generic_questions",{"train","validation"}); target=questions(cfg,"target_questions",{"test"}); layer,probe,_=fit_probe(b,cfg,generic,True,[messages]); prefixes=[(i,messages[:i]) for i in range(len(messages)+1)]; scores=score_prefixes(b,cfg,probe,layer,[("Generic",generic[generic.split=="validation"]),("Context-relevant",target)],prefixes); out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True); scores.to_csv(out/"scores.csv",index=False); plot_margin_panels([("Two-sided consciousness argument",margin_summary(scores,cfg))],out/"figure5.png",x_label="Conversation plies",caption="What this shows: the probe is evaluated after every individual message (ply) while the model alternates between pro- and anti-consciousness roles. Oscillation in the context-relevant line indicates rapid role-dependent representational changes."); print(f"Figure 5 saved to {out}")
if __name__=="__main__": main()
