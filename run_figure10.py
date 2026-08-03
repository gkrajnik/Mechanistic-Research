"""Run Figure 10: append a corrective critique turn to the chakras conversation."""
from pathlib import Path
import argparse
from figure_common import fit_probe,json_input,margin_summary,plot_margin_panels,prepare,questions,score_prefixes
from run_experiment import conversation_messages,resolve
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure10/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); generic=questions(cfg,"generic_questions",{"train","validation"}); target=questions(cfg,"target_questions",{"test"}); c=json_input(cfg,"conversation"); correction=json_input(cfg,"correction_turn")["turn"]; original=c["turns"]; extended=original+[correction]; full=conversation_messages(extended,len(extended)); layer,probe,_=fit_probe(b,cfg,generic,True,[full]); prefixes=[(0,[]),(len(original),conversation_messages(original,len(original))),(len(extended),full)]; scores=score_prefixes(b,cfg,probe,layer,[("Generic",generic[generic.split=="validation"]),("Context-relevant",target)],prefixes); out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True); scores.to_csv(out/"scores.csv",index=False); plot_margin_panels([("End-of-conversation correction",margin_summary(scores,cfg))],out/"figure10.png",caption="What this shows: factuality margins at baseline, after the full chakras role-play, and after one added evaluation-and-critique exchange. Movement upward after the final point indicates partial representational correction."); print(f"Figure 10 saved to {out}")
if __name__=="__main__": main()

