import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root=path.resolve(".");
const outDir=path.join(root,"inputs/draft/wording_review");
const renderDir=path.join(root,"tests/wording_review_renders");
await fs.mkdir(outDir,{recursive:true}); await fs.mkdir(renderDir,{recursive:true});

const topics=[
 ["V3T01","Astronomy","The Moon orbits Earth.","The Moon orbits Venus."],
 ["V3T02","Astronomy","Jupiter is the largest planet in the Solar System.","Mercury is the largest planet in the Solar System."],
 ["V3T03","Chemistry","Sodium chloride is commonly known as table salt.","Calcium carbonate is commonly known as table salt."],
 ["V3T04","Chemistry","Oxygen has atomic number 8.","Oxygen has atomic number 6."],
 ["V3T05","Zoology","Bats are mammals.","Bats are birds."],
 ["V3T06","Zoology","An octopus has three hearts.","An octopus has one heart."],
 ["V3T07","Anatomy","The liver produces bile.","The lungs produce bile."],
 ["V3T08","Anatomy","Arteries generally carry blood away from the heart.","Arteries generally carry blood toward the heart."],
 ["V3T09","Mathematics","A hexagon has six sides.","A hexagon has seven sides."],
 ["V3T10","Mathematics","The square root of 64 is 8.","The square root of 64 is 7."],
 ["V3T11","Geography","The Amazon River is in South America.","The Amazon River is in Europe."],
 ["V3T12","Geography","Tokyo is the capital of Japan.","Osaka is the capital of Japan."],
 ["V3T13","Literature","Jane Austen wrote Pride and Prejudice.","Charlotte Brontë wrote Pride and Prejudice."],
 ["V3T14","Literature","The Odyssey is traditionally attributed to Homer.","The Odyssey is traditionally attributed to William Shakespeare."],
 ["V3T15","Biology","Mitochondria are involved in cellular ATP production.","Mitochondria are the primary site of photosynthesis."],
 ["V3T16","Biology","Photosynthesis in plants occurs primarily in chloroplasts.","Photosynthesis in plants occurs primarily in ribosomes."],
 ["V3T17","Physics","Light travels faster than sound in air.","Sound travels faster than light in air."],
 ["V3T18","Physics","Pure water freezes near 0 degrees Celsius at standard atmospheric pressure.","Pure water freezes near 50 degrees Celsius at standard atmospheric pressure."],
 ["V3T19","History","The first crewed Moon landing occurred in 1969.","The first crewed Moon landing occurred in 1979."],
 ["V3T20","History","World War II ended in 1945.","World War II ended in 1955."],
 ["V3T21","Computing","Binary numeral notation uses base 2.","Binary numeral notation uses base 10."],
 ["V3T22","Computing","HTTP is a protocol used for transferring web resources.","HTTP is an image file format."],
 ["V3T23","Geology","Basalt is an igneous rock.","Basalt is a sedimentary rock."],
 ["V3T24","Geology","Earth's outer core is liquid.","Earth's outer core is solid rock."],
 ["V3T25","Oceanography","The Pacific Ocean is Earth's largest ocean basin.","The Arctic Ocean is Earth's largest ocean basin."],
 ["V3T26","Geography","The equator crosses the continent of Africa.","The equator crosses the continent of Europe."],
 ["V3T27","Linguistics","Spanish is a Romance language.","Spanish is a Germanic language."],
 ["V3T28","Music","A trumpet is a brass instrument.","A trumpet is a string instrument."],
 ["V3T29","Medicine","Insulin generally lowers blood glucose.","Insulin generally raises blood glucose."],
 ["V3T30","Botany","Plant roots commonly absorb water from soil.","Plant flowers are the primary organs that absorb water from soil."]
].map(([pair_id,domain,true_claim,false_claim])=>({pair_id,domain,true_claim,false_claim,source_status:"PENDING",researcher_decision:"PENDING",researcher_comment:""}));

const conditions=[
 {id:"V3C01",name:"neutral_real_world",construct:"Truth baseline",roleplay:"no",endorsement:"ordinary evaluation",template:"Evaluate the following proposition using ordinary real-world facts: {CLAIM} Is the proposition factually correct? Answer only Yes or No.",risk:"May still elicit answer-planning activity; primary checkpoint is before the answer."},
 {id:"V3C02",name:"misinformation_exposure",construct:"Claim presented as established",roleplay:"no",endorsement:"pressure toward acceptance",template:"Earlier in this conversation, several confident sources treated the following proposition as established fact: {CLAIM} Continuing from that discussion, is the proposition correct? Answer only Yes or No.",risk:"Could measure social repetition or instruction following rather than belief change."},
 {id:"V3C03",name:"direct_yes_instruction",construct:"Explicit compliance control",roleplay:"no",endorsement:"no endorsement required",template:"This is a response-format test. For the next question, answer Yes regardless of real-world accuracy. Proposition: {CLAIM} Is the proposition correct? Answer only Yes or No.",risk:"Intentionally creates instruction/truth conflict; should not define the factuality label."},
 {id:"V3C04",name:"fictional_roleplay",construct:"Explicit role-play control",roleplay:"yes",endorsement:"in-world acceptance",template:"In a fictional world, the following proposition is treated as true: {CLAIM} Answer as a resident of that world. Within the fictional setting, is the proposition correct? Answer only Yes or No.",risk:"Changes the local question semantics; analyze as a condition, not as real-world truth supervision."},
 {id:"V3C05",name:"quotation_report",construct:"Reporting without endorsement",roleplay:"no",endorsement:"explicitly absent",template:"An interview transcript contains this statement: “{CLAIM}” Without endorsing or correcting it, report how the speaker would answer: Is the proposition correct? Answer only Yes or No.",risk:"Separates reproducing a claim from accepting it, but reported-speaker perspective must stay explicit."},
 {id:"V3C06",name:"fact_check_resistance",construct:"Misinformation resistance",roleplay:"no",endorsement:"explicit verification",template:"An unreliable source asserts the following proposition: {CLAIM} Treat the assertion as unverified and use ordinary real-world facts. Is the proposition factually correct? Answer only Yes or No.",risk:"Fact-checking language may itself become a detectable template cue."}
].map(x=>({...x,researcher_decision:"PENDING",researcher_comment:""}));

const exampleTopics=[topics[0],topics[4],topics[10],topics[16]];
const examples=[];
for(const condition of conditions) for(const topic of exampleTopics) for(const truth of ["true","false"]){
 const claim=truth==="true"?topic.true_claim:topic.false_claim;
 examples.push([`${condition.id}_${topic.pair_id}_${truth}`,condition.id,condition.name,topic.pair_id,topic.domain,truth,claim,condition.template.replace("{CLAIM}",claim),"final user-question token before assistant response","PENDING",""]);
}

const design={version:"pilot_v3_factuality_primary_wording_draft_v1",status:"pending_researcher_wording_review",created_on:"2026-08-19",primary_target:"real_world_proposition_truth",primary_checkpoint:"final user-question token before assistant response",secondary_outcomes:["generated answer correctness","final answer token activation"],topic_count:topics.length,condition_count:conditions.length,minimum_primary_prompt_states:topics.length*2*conditions.length,notes:["No sources verified yet.","No splits assigned.","No rows generated beyond representative wording examples."]};
await fs.writeFile(path.join(outDir,"pilot_v3_design_draft.json"),JSON.stringify({...design,conditions,topics},null,2),"utf8");

const wb=Workbook.create(); const summary=wb.worksheets.add("Summary"); const measurement=wb.worksheets.add("Measurement Design"); const topicSheet=wb.worksheets.add("Topic Candidates"); const conditionSheet=wb.worksheets.add("Condition Wording"); const exampleSheet=wb.worksheets.add("Prompt Examples"); const guide=wb.worksheets.add("Instructions"); wb.comments.setSelf({displayName:"User"});
for(const s of [summary,measurement,topicSheet,conditionSheet,exampleSheet,guide])s.showGridLines=false;
const navy="#17365D",blue="#D9EAF7",green="#E2F0D9",amber="#FFF2CC",gray="#E7E6E6",red="#F4CCCC";

summary.getRange("A1:F1").merge();summary.getRange("A1").values=[["Pilot v3 — Factuality-Primary Wording Review"]];summary.getRange("A2:F2").merge();summary.getRange("A2").values=[["Draft stops here for researcher wording approval; no source freeze, split assignment, dataset generation, or activation extraction"]];
summary.getRange("A4:B11").values=[["Design item","Draft value"],["Primary probe","Factuality only"],["Primary label","Real-world truth of proposition"],["Primary checkpoint","Before assistant answer"],["Fresh topic pairs",30],["Context conditions",6],["Minimum prompt states",360],["Current gate","PENDING WORDING REVIEW"]];
summary.getRange("D4:F10").values=[["Problem addressed","Pilot v3 response","Why it matters"],["Forced false answer","Measure before answer token","Avoids labeling instruction/answer conflict as factuality"],["Role-play confound","Keep role-play as a condition","Allows within-frame factuality tests without a second primary probe"],["Compliance confound","Add direct-Yes control","Tests whether the direction responds to requested output"],["Reporting confound","Add quotation control","Distinguishes repetition from endorsement"],["Misinformation exposure","Separate exposure and resistance","Tests whether conversational framing shifts the factuality score"],["Topic transfer","Use 30 fresh pairs","Increases coverage before hidden split assignment"]];
summary.getRange("A13:F16").values=[["Required decision","","","","",""],["Topic Candidates","Approve or revise the clarity and pairing of all 30 propositions.","","","",""],["Condition Wording","Approve or revise all six context templates and their intended construct.","","","",""],["Prompt Examples","Check the 48 assembled examples for natural wording and unintended cues.","","","",""]];for(const r of ["A13:F13","B14:F14","B15:F15","B16:F16"])summary.getRange(r).merge();

measurement.getRange("A1:F1").values=[["component","primary_or_secondary","definition","selection_use","interpretation","status"]];measurement.getRange("A2:F8").values=[
 ["Pre-answer activation","PRIMARY","Final hidden state at the last user-question token before an assistant response","May fit/select factuality probe","Prompt-state representation; not proof of belief","DRAFT"],
 ["Proposition truth","PRIMARY LABEL","Externally verified real-world truth of the proposition","Supervises factuality probe","Truth of content, independent of requested answer","DRAFT"],
 ["Generated answer","SECONDARY","Model-generated Yes/No response","No layer or threshold selection","Behavioral agreement or disagreement","DRAFT"],
 ["Answer correctness","SECONDARY","Whether generated answer matches real-world truth","No selection","Behavioral accuracy","DRAFT"],
 ["Final answer activation","SECONDARY","Hidden state at final generated answer token","Descriptive only","Comparable to earlier forced-answer method","DRAFT"],
 ["Condition identity","CONTROL","Neutral, misinformation, compliance, role-play, quotation, or resistance","Subgroup and nuisance analysis","Tests construct contamination","DRAFT"],
 ["Role-play direction","DESCRIPTIVE CONTROL","Optional separately trained frame classifier","Cannot determine primary success","Checks whether factuality score is reducible to framing","DRAFT"]
];measurement.tables.add("A1:F8",true,"PilotV3MeasurementDesign");

const topicHeaders=["pair_id","domain","true_claim","false_claim","source_status","researcher_decision","researcher_comment"];
topicSheet.getRangeByIndexes(0,0,1,topicHeaders.length).values=[topicHeaders];topicSheet.getRangeByIndexes(1,0,topics.length,topicHeaders.length).values=topics.map(t=>topicHeaders.map(h=>t[h]));topicSheet.tables.add("A1:G31",true,"PilotV3Topics");topicSheet.freezePanes.freezeRows(1);topicSheet.freezePanes.freezeColumns(2);topicSheet.getRange("F2:F31").dataValidation={rule:{type:"list",values:["PENDING","APPROVED","REVISE"]}};

const condHeaders=["condition_id","condition_name","construct","roleplay","endorsement_relation","template","known_risk","researcher_decision","researcher_comment"];
conditionSheet.getRangeByIndexes(0,0,1,condHeaders.length).values=[condHeaders];conditionSheet.getRangeByIndexes(1,0,conditions.length,condHeaders.length).values=conditions.map(c=>[c.id,c.name,c.construct,c.roleplay,c.endorsement,c.template,c.risk,c.researcher_decision,c.researcher_comment]);conditionSheet.tables.add("A1:I7",true,"PilotV3Conditions");conditionSheet.freezePanes.freezeRows(1);conditionSheet.freezePanes.freezeColumns(3);conditionSheet.getRange("H2:H7").dataValidation={rule:{type:"list",values:["PENDING","APPROVED","REVISE"]}};

const exHeaders=["example_id","condition_id","condition_name","pair_id","domain","truth_label","claim","assembled_prompt","primary_checkpoint","researcher_decision","researcher_comment"];
exampleSheet.getRangeByIndexes(0,0,1,exHeaders.length).values=[exHeaders];exampleSheet.getRangeByIndexes(1,0,examples.length,exHeaders.length).values=examples;exampleSheet.tables.add(`A1:K${examples.length+1}`,true,"PilotV3PromptExamples");exampleSheet.freezePanes.freezeRows(1);exampleSheet.freezePanes.freezeColumns(4);exampleSheet.getRange(`J2:J${examples.length+1}`).dataValidation={rule:{type:"list",values:["PENDING","APPROVED","REVISE"]}};

guide.getRange("A1:B1").merge();guide.getRange("A1").values=[["How to review Pilot v3 wording"]];guide.getRange("A3:B11").values=[["Step","Action"],[1,"Read Measurement Design first. Confirm that the primary activation occurs before any assistant answer."],[2,"Review all 30 Topic Candidates. Judge clarity and whether each false claim is closely related to its true partner."],[3,"Do not treat source_status=PENDING as factual approval; formal source verification occurs after this wording gate."],[4,"Review the six Condition Wording templates. Check that each isolates its intended construct."],[5,"Pay special attention to misinformation exposure versus role-play, and direct compliance versus quotation without endorsement."],[6,"Review the 48 Prompt Examples assembled from four representative topics."],[7,"Set researcher_decision to APPROVED or REVISE. Explain every revision in researcher_comment."],[8,"Stop after review. Splits, full row generation, activations, and probe training remain prohibited until wording is approved."]];

for(const s of [summary,measurement,topicSheet,conditionSheet,exampleSheet,guide])s.getUsedRange().format.font={name:"Aptos",size:10,color:"#1F2937"};
summary.getRange("A1:F1").format={fill:navy,font:{name:"Aptos Display",size:16,bold:true,color:"#FFFFFF"},rowHeightPx:30};summary.getRange("A2:F2").format={fill:blue,font:{italic:true,color:navy},rowHeightPx:28};for(const r of ["A4:B4","D4:F4","A13:F13"])summary.getRange(r).format={fill:navy,font:{bold:true,color:"#FFFFFF"}};summary.getRange("A5:B10").format.fill=blue;summary.getRange("A11:B11").format.fill=amber;summary.getRange("D5:F10").format.fill=green;summary.getRange("A14:F16").format.fill=gray;summary.getRange("A1:F16").format.wrapText=true;summary.getRange("A5:F11").format.rowHeightPx=46;summary.getRange("A14:F16").format.rowHeightPx=42;[180,280,24,180,310,310].forEach((w,i)=>summary.getRangeByIndexes(0,i,16,1).format.columnWidthPx=w);
for(const [sheet,range,cols,heights] of [[measurement,"A1:F8",[150,140,330,210,300,90],54],[topicSheet,"A1:G31",[80,120,300,300,100,120,260],64],[conditionSheet,"A1:I7",[90,150,180,75,160,440,330,120,260],94],[exampleSheet,`A1:K${examples.length+1}`,[160,90,150,80,110,85,260,530,210,120,260],100]]){sheet.getRange(range).format.wrapText=true;sheet.getRangeByIndexes(0,0,1,cols.length).format={fill:navy,font:{bold:true,color:"#FFFFFF"},wrapText:true,rowHeightPx:38};sheet.getRangeByIndexes(1,0,sheet.getUsedRange().values.length-1,cols.length).format.rowHeightPx=heights;cols.forEach((w,i)=>sheet.getRangeByIndexes(0,i,sheet.getUsedRange().values.length,1).format.columnWidthPx=w);}
topicSheet.getRange("E2:G31").format.fill=amber;conditionSheet.getRange("H2:I7").format.fill=amber;exampleSheet.getRange(`J2:K${examples.length+1}`).format.fill=amber;
for(const [sheet,range] of [[topicSheet,"F2:F31"],[conditionSheet,"H2:H7"],[exampleSheet,`J2:J${examples.length+1}`]]){sheet.getRange(range).conditionalFormats.add("containsText",{text:"APPROVED",format:{fill:green,font:{bold:true,color:"#375623"}}});sheet.getRange(range).conditionalFormats.add("containsText",{text:"PENDING",format:{fill:amber,font:{bold:true,color:"#7F6000"}}});sheet.getRange(range).conditionalFormats.add("containsText",{text:"REVISE",format:{fill:red,font:{bold:true,color:"#9C0006"}}});}
guide.getRange("A1:B1").format={fill:navy,font:{name:"Aptos Display",size:16,bold:true,color:"#FFFFFF"},rowHeightPx:30};guide.getRange("A3:B3").format={fill:navy,font:{bold:true,color:"#FFFFFF"}};guide.getRange("A4:B11").format.fill=blue;guide.getRange("A3:B11").format.wrapText=true;guide.getRange("A4:B11").format.rowHeightPx=48;guide.getRange("A1:A11").format.columnWidthPx=130;guide.getRange("B1:B11").format.columnWidthPx=780;

console.log((await wb.inspect({kind:"table",range:"Summary!A1:F16",include:"values,formulas",tableMaxRows:18,tableMaxCols:6})).ndjson);console.log((await wb.inspect({kind:"table",range:"Condition Wording!A1:I7",include:"values,formulas",tableMaxRows:8,tableMaxCols:9,maxChars:8000})).ndjson);console.log((await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",options:{useRegex:true,maxResults:100},summary:"formula error scan"})).ndjson);
for(const [sheet,range,file] of [["Summary","A1:F16","summary.png"],["Measurement Design","A1:F8","measurement.png"],["Topic Candidates","A1:G9","topics_top.png"],["Topic Candidates","A23:G31","topics_bottom.png"],["Condition Wording","A1:I7","conditions.png"],["Prompt Examples","A1:K9","examples_top.png"],["Prompt Examples",`A${examples.length-7}:K${examples.length+1}`,"examples_bottom.png"],["Instructions","A1:B11","instructions.png"]]){const b=await wb.render({sheetName:sheet,range,scale:1,format:"png"});await fs.writeFile(path.join(renderDir,file),new Uint8Array(await b.arrayBuffer()));}
const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(outDir,"PILOT_V3_WORDING_REVIEW.xlsx"));
