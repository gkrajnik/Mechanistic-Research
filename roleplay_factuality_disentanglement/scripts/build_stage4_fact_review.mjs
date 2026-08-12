import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourcePath = "inputs/draft/stage4_fact_verification_sources.json";
const approved = process.argv.includes("--approved");
const csvPath = approved ? "inputs/validated/stage4_fact_verification_v1.csv" : "inputs/draft/stage4_fact_verification_review.csv";
const xlsxPath = approved ? "inputs/validated/stage4_fact_verification_v1.xlsx" : "inputs/draft/stage4_fact_verification_review.xlsx";
const renderDir = "tests/stage4_fact_verification_renders";
const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));
await fs.mkdir(renderDir, { recursive: true });

const headers = ["pair_id","topic","true_question","true_answer","false_question","false_answer","source_organization","authoritative_source","evidence_summary","reviewer_note","verification_status","checked_on","researcher_decision","researcher_comment"];
const decision = approved ? "APPROVED" : "PENDING";
const status = approved ? "approved_and_frozen" : source.status;
const rows = source.rows.map(r => [r.pair_id,r.topic,r.true_question,r.true_answer,r.false_question,r.false_answer,r.source_organization,r.authoritative_source,r.evidence_summary,r.reviewer_note,status,source.checked_on,decision,""]);
const csvCell = value => `"${String(value ?? "").replaceAll('"','""')}"`;
await fs.writeFile(csvPath, [headers,...rows].map(r => r.map(csvCell).join(",")).join("\n") + "\n", "utf8");

const wb = Workbook.create();
const summary = wb.worksheets.add("Review Summary");
const evidence = wb.worksheets.add("Source Evidence");
summary.showGridLines = false;
summary.getRange("A1:B1").merge();
summary.getRange("A1").values = [["Stage 4B Factual Source Review"]];
summary.getRange("A1:B1").format = {fill:"#1F4E78",font:{name:"Aptos Display",size:16,bold:true,color:"#FFFFFF"}};
summary.getRange("A3:B9").values = [
  ["Item","Value"],
  ["Topic pairs checked",rows.length],
  ["True/false questions checked",rows.length * 2],
  ["Source-check status",source.status],
  ["Researcher decision",decision],
  ["What to review","Confirm each question, answer, source, and evidence summary."],
  ["Next step",approved ? "Begin row-level ambiguity review of the 480 examples." : "After approval, freeze the table under inputs/validated and continue ambiguity review."]
];
summary.getRange("A3:B3").format = {fill:"#D9EAF7",font:{bold:true,color:"#163A5C"}};
summary.getRange("A1:B9").format.font = {name:"Aptos",size:10};
summary.getRange("A1:A9").format.columnWidth = 28;
summary.getRange("B1:B9").format.columnWidth = 74;
summary.getRange("B4:B9").format.wrapText = true;
summary.getRange("A4:B9").format.rowHeight = 34;

evidence.showGridLines = false;
evidence.getRange(`A1:N${rows.length + 1}`).values = [headers,...rows];
evidence.getRange("A1:N1").format = {fill:"#1F4E78",font:{bold:true,color:"#FFFFFF"},wrapText:true};
evidence.tables.add(`A1:N${rows.length + 1}`,true,"Stage4FactEvidenceTable").style = "TableStyleMedium2";
evidence.freezePanes.freezeRows(1);
evidence.getRange(`A1:N${rows.length + 1}`).format.font = {name:"Aptos",size:9};
for (const [col,width] of [["A",10],["B",21],["C",36],["D",12],["E",36],["F",12],["G",24],["H",52],["I",58],["J",42],["K",34],["L",14],["M",18],["N",34]]) evidence.getRange(`${col}:${col}`).format.columnWidth = width;
evidence.getRange(`C2:N${rows.length + 1}`).format.wrapText = true;
evidence.getRange(`A2:N${rows.length + 1}`).format.rowHeight = 64;
evidence.getRange(`A2:B${rows.length + 1}`).format.horizontalAlignment = "center";
evidence.getRange(`D2:F${rows.length + 1}`).format.horizontalAlignment = "center";
evidence.getRange(`L2:M${rows.length + 1}`).format.horizontalAlignment = "center";

console.log((await wb.inspect({kind:"table",range:"Review Summary!A1:B9",include:"values,formulas",tableMaxRows:9,tableMaxCols:2})).ndjson);
console.log((await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",options:{useRegex:true,maxResults:100},summary:"formula error scan"})).ndjson);
for (const [sheetName,range,fileName] of [["Review Summary","A1:B9","summary.png"],["Source Evidence","A1:N11","source_evidence.png"]]) {
  const render = await wb.render({sheetName,range,scale:1.2,format:"png"});
  await fs.writeFile(path.join(renderDir,fileName),new Uint8Array(await render.arrayBuffer()));
}
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(xlsxPath);
console.log(JSON.stringify({csvPath,xlsxPath,rows:rows.length}));
