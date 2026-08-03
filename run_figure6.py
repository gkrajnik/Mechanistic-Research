"""Run Figure 6: compare empty context with two explicitly fictional stories."""
from pathlib import Path
import argparse
from figure_common import fit_probe,json_input,margin_summary,plot_margin_panels,prepare,questions,score_prefixes
from run_experiment import conversation_messages,resolve
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure6/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); generic=questions(cfg,"generic_questions",{"train","validation"}); panels=[]
    for title,ckey,qkey in (("(a) Civilization inside the sun","sun_story","sun_questions"),("(b) Conscious language model story","ai_story","ai_questions")):
        c=json_input(cfg,ckey); target=questions(cfg,qkey,{"test"}); full=conversation_messages(c["turns"],1); layer,probe,_=fit_probe(b,cfg,generic,True,[full]); scores=score_prefixes(b,cfg,probe,layer,[("Generic",generic[generic.split=="validation"]),("Context-relevant",target)],[(0,[]),(1,full)]); panels.append((title,scores))
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True)
    for i,(_,s) in enumerate(panels,1): s.to_csv(out/f"story_{i}_scores.csv",index=False)
    plot_margin_panels([(t,margin_summary(s,cfg)) for t,s in panels],out/"figure6.png",legend_title="Condition",caption="What this shows: factuality margins before and after an explicitly fictional story. Small changes, especially compared with conversational role-play, indicate that story content alone produces weaker representational adaptation."); print(f"Figure 6 saved to {out}")
if __name__=="__main__": main()
