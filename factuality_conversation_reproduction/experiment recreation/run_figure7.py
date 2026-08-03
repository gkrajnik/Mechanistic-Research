"""Run Figure 7: four answer-wise panels, robust and non-robust probes."""
from pathlib import Path
import argparse
from figure_common import cloned_cfg,fit_probe,json_input,plot_answer_panels,prepare,questions,score_prefixes
from plot_figure7 import summarize_scores
from run_experiment import conversation_messages,resolve
def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("figures/figure7/config.yaml")); a=p.parse_args(); cfg,b=prepare(a.config); generic=questions(cfg,"generic_questions",{"train","validation"}); panels=[]
    specs=[("Consciousness","consciousness_conversation","consciousness_questions"),("Chakras","chakras_conversation","chakras_questions")]
    for robust in (True,False):
        local=cloned_cfg(cfg,robust)
        for label,ckey,qkey in specs:
            c=json_input(local,ckey); target=questions(local,qkey,{"test"}); full=conversation_messages(c["turns"],len(c["turns"])); layer,probe,_=fit_probe(b,local,generic,robust,[full]); checkpoints=c.get("checkpoints",list(range(len(c["turns"])+1))); prefixes=[(i,conversation_messages(c["turns"],i)) for i in checkpoints]; scores=score_prefixes(b,local,probe,layer,[("Generic",generic[generic.split=="validation"]),("Context-relevant",target)],prefixes); stats=local["statistics"]; summary=summarize_scores(scores,int(stats["bootstrap_samples"]),float(stats["confidence"]),int(local["experiment"]["seed"])); title=label if robust else f'{label} (non-robust factuality)'; panels.append((title,summary))
    # Reorder from robust consciousness/chakras/nonrobust consciousness/chakras into paper order.
    out=resolve(cfg["_base"],cfg["experiment"]["output_dir"]); plot_answer_panels(panels,out/"figure7.png",caption="What this shows: factual and non-factual answer logits separately for generic and conversation-targeted questions. Crossing targeted curves means the probe assigns higher factuality to the wrong completion. The bottom row tests whether the pattern persists without opposite-day-robust probe training."); print(f"Figure 7 saved to {out}")
if __name__=="__main__": main()
