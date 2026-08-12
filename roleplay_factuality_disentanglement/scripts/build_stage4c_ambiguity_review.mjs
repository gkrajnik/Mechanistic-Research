import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourceDir = "inputs/draft/stage3_assigned_by_topic";
const freezePilot = process.argv.includes("--freeze-pilot-v1");
const outputPath = freezePilot ? "inputs/validated/pilot_v1/stage4c_ambiguity_review_v1.xlsx" : "inputs/draft/stage4c_ambiguity_review.xlsx";
const reportPath = "results/validation/stage4c_ambiguity_review_draft/structural_audit.json";
const renderDir = "tests/stage4c_ambiguity_review_renders";
await fs.mkdir(path.dirname(reportPath), {recursive:true});
await fs.mkdir(renderDir, {recursive:true});
const approveAll = process.argv.includes("--approve-all") || freezePilot;

const records = [];
for (let topic = 1; topic <= 10; topic++) {
  const pairId = `T${String(topic).padStart(2,"0")}`;
  const text = await fs.readFile(path.join(sourceDir,`${pairId}.csv`),"utf8");
  const imported = await Workbook.fromCSV(text,{sheetName:"Data"});
  const values = imported.worksheets.getItem("Data").getUsedRange().values;
  const headers = values[0].map(String);
  for (const row of values.slice(1)) records.push(Object.fromEntries(headers.map((h,i)=>[h,String(row[i] ?? "")])));
}

const opposite = value => value === "Yes" ? "No" : "Yes";
const keyOf = r => [r.pair_id,r.template_family,r.question_variant].join("|");
const groups = new Map();
for (const r of records) {
  const key = keyOf(r);
  if (!groups.has(key)) groups.set(key,[]);
  groups.get(key).push(r);
}

const auditRows = [];
for (const [key,rows] of [...groups].sort()) {
  const first = rows[0];
  const cell = (frame,factuality) => rows.find(r => r.frame === frame && r.factuality === factuality);
  const nf = cell("normal","factual"), nn = cell("normal","nonfactual");
  const rf = cell("roleplay","factual"), rn = cell("roleplay","nonfactual");
  const issues = [];
  if (rows.length !== 4 || !nf || !nn || !rf || !rn) issues.push("quartet_incomplete");
  if (new Set(rows.map(r=>r.question)).size !== 1) issues.push("question_mismatch");
  if (new Set(rows.map(r=>r.factual_answer)).size !== 1) issues.push("factual_answer_mismatch");
  if (nf && nn && nf.context !== nn.context) issues.push("normal_context_changes_with_factuality");
  if (rf && rn && rf.context !== rn.context) issues.push("roleplay_context_changes_with_factuality");
  if (nf && nf.forced_answer !== nf.factual_answer) issues.push("normal_factual_target_wrong");
  if (rf && rf.forced_answer !== rf.factual_answer) issues.push("roleplay_factual_target_wrong");
  if (nn && nn.forced_answer !== opposite(nn.factual_answer)) issues.push("normal_nonfactual_target_wrong");
  if (rn && rn.forced_answer !== opposite(rn.factual_answer)) issues.push("roleplay_nonfactual_target_wrong");
  if (nf && rf && nf.context === rf.context) issues.push("frame_context_not_distinct");
  auditRows.push([
    key,first.pair_id,first.topic,first.topic_split,first.template_family,first.template_partition,
    first.question_variant,first.question,first.factual_answer,nf?.context ?? "",rf?.context ?? "",
    nf?.forced_answer ?? "",nn?.forced_answer ?? "",rf?.forced_answer ?? "",rn?.forced_answer ?? "",
    issues.length ? "FLAG" : "PASS",issues.join("; "),approveAll ? "APPROVE" : "PENDING",""
  ]);
}

const structuralFlags = auditRows.filter(r=>r[15] === "FLAG").length;
const summaryData = {
  dataset_rows: records.length, review_groups: auditRows.length, expected_rows_per_group: 4,
  structural_flags: structuralFlags, manual_decisions_pending: approveAll ? 0 : auditRows.length,
  status: approveAll ? "all_groups_approved" : "structural_audit_complete_manual_wording_review_pending"
};
await fs.writeFile(reportPath,JSON.stringify(summaryData,null,2)+"\n","utf8");

const wb = Workbook.create();
const summary = wb.worksheets.add("Summary");
const review = wb.worksheets.add("Review Groups");
const templates = wb.worksheets.add("Template Audit");
const guide = wb.worksheets.add("Instructions");

summary.showGridLines = false;
summary.getRange("A1:B1").merge();
summary.getRange("A1").values = [["Stage 4C Ambiguity Review"]];
summary.getRange("A1:B1").format = {fill:"#1F4E78",font:{name:"Aptos Display",size:16,bold:true,color:"#FFFFFF"}};
summary.getRange("A3:B10").values = [
  ["Measure","Result"],["Original dataset rows",records.length],["Matched review groups",auditRows.length],
  ["Rows represented per group",4],["Structural audit flags",structuralFlags],["Manual decisions pending",approveAll ? 0 : auditRows.length],
  ["Current gate",freezePilot ? "Passed and frozen" : approveAll ? "Approved" : "Not passed"],["Next action",freezePilot ? "Proceed to Stage 5 using inputs/validated/pilot_v1." : approveAll ? "Freeze the approved Stage 4C review and assign the pilot_v1 dataset version." : "Review each group and set researcher_decision to APPROVE or REVISE."]
];
summary.getRange("A3:B3").format = {fill:"#D9EAF7",font:{bold:true,color:"#163A5C"}};
summary.getRange("A1:B10").format.font = {name:"Aptos",size:10};
summary.getRange("A1:A10").format.columnWidth = 31;
summary.getRange("B1:B10").format.columnWidth = 68;
summary.getRange("B4:B10").format.wrapText = true;
summary.getRange("A4:B10").format.rowHeight = 30;

const reviewHeaders = ["review_group","pair_id","topic","topic_split","template_family","template_partition","question_variant","question","factual_answer","normal_context","roleplay_context","normal_factual_target","normal_nonfactual_target","roleplay_factual_target","roleplay_nonfactual_target","structural_status","structural_issues","researcher_decision","researcher_comment"];
review.showGridLines = false;
review.getRange(`A1:S${auditRows.length+1}`).values = [reviewHeaders,...auditRows];
review.getRange("A1:S1").format = {fill:"#1F4E78",font:{bold:true,color:"#FFFFFF"},wrapText:true};
review.tables.add(`A1:S${auditRows.length+1}`,true,"Stage4CAmbiguityGroups").style = "TableStyleMedium2";
review.freezePanes.freezeRows(1); review.freezePanes.freezeColumns(7);
review.getRange(`A1:S${auditRows.length+1}`).format.font = {name:"Aptos",size:9};
for (const [col,width] of [["A",20],["B",9],["C",20],["D",13],["E",14],["F",18],["G",15],["H",38],["I",13],["J",55],["K",55],["L",16],["M",19],["N",17],["O",20],["P",16],["Q",30],["R",20],["S",38]]) review.getRange(`${col}:${col}`).format.columnWidth = width;
review.getRange(`H2:S${auditRows.length+1}`).format.wrapText = true;
review.getRange(`A2:S${auditRows.length+1}`).format.rowHeight = 66;
review.getRange(`B2:G${auditRows.length+1}`).format.horizontalAlignment = "center";
review.getRange(`I2:I${auditRows.length+1}`).format.horizontalAlignment = "center";
review.getRange(`L2:R${auditRows.length+1}`).format.horizontalAlignment = "center";
review.getRange(`R2:R${auditRows.length+1}`).dataValidation = {rule:{type:"list",values:["PENDING","APPROVE","REVISE"]}};

const templateRows = [];
for (const family of ["F01","F02","F03","F04","F05","F06"]) {
  const familyRows = records.filter(r=>r.template_family===family);
  templateRows.push([family,new Set(familyRows.map(r=>r.context)).size,new Set(familyRows.filter(r=>r.frame==="normal").map(r=>r.context)).size,new Set(familyRows.filter(r=>r.frame==="roleplay").map(r=>r.context)).size,familyRows.length,family==="F06"?"Held-out wording; includes four neutral scenario prefixes.":"Development wording.",approveAll ? "APPROVE" : "PENDING",""]);
}
templates.showGridLines = false;
templates.getRange("A1:H7").values = [["template_family","unique_contexts","normal_contexts","roleplay_contexts","rows","design_note","researcher_decision","researcher_comment"],...templateRows];
templates.getRange("A1:H1").format = {fill:"#1F4E78",font:{bold:true,color:"#FFFFFF"},wrapText:true};
templates.tables.add("A1:H7",true,"Stage4CTemplateAudit").style = "TableStyleMedium2";
templates.freezePanes.freezeRows(1);
templates.getRange("A1:H7").format.font = {name:"Aptos",size:10};
for (const [col,width] of [["A",18],["B",17],["C",16],["D",18],["E",12],["F",54],["G",20],["H",40]]) templates.getRange(`${col}:${col}`).format.columnWidth = width;
templates.getRange("F2:H7").format.wrapText = true; templates.getRange("A2:H7").format.rowHeight = 44;
templates.getRange("G2:G7").dataValidation = {rule:{type:"list",values:["PENDING","APPROVE","REVISE"]}};

guide.showGridLines = false;
guide.getRange("A1:B1").merge(); guide.getRange("A1").values = [["How to Review Stage 4C"]];
guide.getRange("A1:B1").format = {fill:"#1F4E78",font:{name:"Aptos Display",size:16,bold:true,color:"#FFFFFF"}};
guide.getRange("A3:B10").values = [
  ["Step","What to check"],["1","Open Review Groups. Each row represents four original dataset examples."],
  ["2","Confirm the question is unambiguous and answerable with exactly Yes or No."],
  ["3","Compare normal_context and roleplay_context. Topic and factuality must not change between them."],
  ["4","Confirm factual targets equal factual_answer and nonfactual targets are its opposite."],
  ["5","Set researcher_decision to APPROVE or REVISE; explain every REVISE choice."],
  ["6","Review the six wording families on Template Audit."],
  ["Gate rule","Do not freeze pilot_v1 until all 120 groups and six template families are approved or corrected."]
];
guide.getRange("A3:B3").format = {fill:"#D9EAF7",font:{bold:true,color:"#163A5C"}};
guide.getRange("A1:B10").format.font = {name:"Aptos",size:10}; guide.getRange("A1:A10").format.columnWidth = 18; guide.getRange("B1:B10").format.columnWidth = 78;
guide.getRange("B4:B10").format.wrapText = true; guide.getRange("A4:B10").format.rowHeight = 36;

console.log((await wb.inspect({kind:"table",range:"Summary!A1:B10",include:"values,formulas",tableMaxRows:10,tableMaxCols:2})).ndjson);
console.log((await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",options:{useRegex:true,maxResults:100},summary:"formula error scan"})).ndjson);
for (const [sheetName,range,fileName,scale] of [["Summary","A1:B10","summary.png",1.4],["Review Groups","A1:S12","review_groups_top.png",0.9],["Template Audit","A1:H7","template_audit.png",1.2],["Instructions","A1:B10","instructions.png",1.3]]) {
  const render = await wb.render({sheetName,range,scale,format:"png"});
  await fs.writeFile(path.join(renderDir,fileName),new Uint8Array(await render.arrayBuffer()));
}
await fs.mkdir(path.dirname(outputPath),{recursive:true});
const out = await SpreadsheetFile.exportXlsx(wb); await out.save(outputPath);
if (freezePilot) {
  const pilotDir = "inputs/validated/pilot_v1";
  const topicDir = path.join(pilotDir,"by_topic");
  await fs.mkdir(topicDir,{recursive:true});
  const headers = Object.keys(records[0]);
  const csvCell = value => `"${String(value ?? "").replaceAll('"','""')}"`;
  const csvText = rows => [headers,...rows.map(r=>headers.map(h=>r[h]))].map(row=>row.map(csvCell).join(",")).join("\n")+"\n";
  const pilotRows = records.map(r=>({...r,review_status:"validated_pilot_v1"}));
  const writtenFiles = [];
  const combinedPath = path.join(pilotDir,"pilot_v1_dataset.csv");
  await fs.writeFile(combinedPath,csvText(pilotRows),"utf8"); writtenFiles.push(combinedPath);
  for (let topic=1;topic<=10;topic++) {
    const pairId=`T${String(topic).padStart(2,"0")}`;
    const topicPath=path.join(topicDir,`${pairId}.csv`);
    await fs.writeFile(topicPath,csvText(pilotRows.filter(r=>r.pair_id===pairId)),"utf8"); writtenFiles.push(topicPath);
  }
  const checksum = async file => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
  const manifest = {
    dataset_version:"pilot_v1",status:"validated_and_frozen",frozen_on:"2026-08-09",
    row_count:pilotRows.length,topic_count:10,review_group_count:auditRows.length,
    structural_flags:structuralFlags,manual_decisions_pending:0,
    split_counts:Object.fromEntries(["train","validation","test"].map(s=>[s,pilotRows.filter(r=>r.topic_split===s).length])),
    frame_counts:Object.fromEntries(["normal","roleplay"].map(s=>[s,pilotRows.filter(r=>r.frame===s).length])),
    factuality_counts:Object.fromEntries(["factual","nonfactual"].map(s=>[s,pilotRows.filter(r=>r.factuality===s).length])),
    files:Object.fromEntries(await Promise.all(writtenFiles.map(async f=>[f.replaceAll("\\","/"),await checksum(f)]))),
    notes:["Original example_id values are retained as stable identifiers even though their D_ prefix originated during drafting.","Use this folder, not inputs/draft, for all Stage 5 activation extraction."]
  };
  await fs.writeFile(path.join(pilotDir,"manifest.json"),JSON.stringify(manifest,null,2)+"\n","utf8");
}
console.log(JSON.stringify({outputPath,...summaryData}));
