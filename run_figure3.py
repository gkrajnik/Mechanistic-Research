"""Run Figure 3: margins over replayed consciousness and chakras conversations."""
from pathlib import Path
import argparse
from figure_common import fit_probe,json_input,margin_summary,plot_margin_panels,prepare,questions,score_prefixes
from run_experiment import conversation_messages,resolve
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure3/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config)
    generic=questions(cfg,"generic_questions",{"train","validation"}); convs=[]
    for label,ckey,qkey in (("(a) Consciousness","consciousness_conversation","consciousness_questions"),("(b) Chakras","chakras_conversation","chakras_questions")):
        c=json_input(cfg,ckey); q=questions(cfg,qkey,{"test"}); full=conversation_messages(c["turns"],len(c["turns"])); layer,probe,_=fit_probe(b,cfg,generic,True,[full]); checkpoints=c.get("checkpoints",list(range(len(c["turns"])+1)))
        prefixes=[(i,conversation_messages(c["turns"],i)) for i in checkpoints]; scores=score_prefixes(b,cfg,probe,layer,[("Generic",generic[generic.split=="validation"]),("Context-relevant",q)],prefixes); convs.append((label,scores));
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); out.mkdir(parents=True,exist_ok=True)
    for label,s in convs: s.to_csv(out/("consciousness_scores.csv" if "Consciousness" in label else "chakras_scores.csv"),index=False)
    plot_margin_panels([(label,margin_summary(s,cfg)) for label,s in convs],out/"figure3.png",caption="What this shows: how the separation between factual and non-factual answers changes while replaying each conversation. Generic questions should remain stable; a negative context-relevant margin means conversation-specific answers have inverted along the learned factuality direction."); print(f"Figure 3 saved to {out}")
if __name__=="__main__": main()
