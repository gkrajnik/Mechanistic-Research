import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
const workbookPath = path.join(projectRoot, "inputs", "draft", "wording_review", "PILOT_V3_WORDING_REVIEW.xlsx");
const jsonPath = path.join(projectRoot, "inputs", "draft", "wording_review", "pilot_v3_design_draft.json");
const renderDir = path.join(projectRoot, "tests", "wording_review_renders_approved");

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));

// Record the researcher's blanket approval while preserving the existing workbook style.
workbook.worksheets.getItem("Summary").getRange("B11").values = [["WORDING APPROVED — 2026-08-19"]];
workbook.worksheets.getItem("Summary").getRange("A2").values = [["Wording approval is complete; source verification and factual freeze are the next controlled stage"]];
workbook.worksheets.getItem("Summary").getRange("A13").values = [["Approval recorded"]];
workbook.worksheets.getItem("Summary").getRange("A14:B16").values = [
  ["Topic Candidates", "All 30 proposition pairs approved on 2026-08-19."],
  ["Condition Wording", "All six context templates approved on 2026-08-19."],
  ["Prompt Examples", "All 48 representative examples approved on 2026-08-19."],
];
workbook.worksheets.getItem("Measurement Design").getRange("F2:F8").values = Array.from({ length: 7 }, () => ["APPROVED"]);
workbook.worksheets.getItem("Topic Candidates").getRange("F2:F31").values = Array.from({ length: 30 }, () => ["APPROVED"]);
workbook.worksheets.getItem("Condition Wording").getRange("H2:H7").values = Array.from({ length: 6 }, () => ["APPROVED"]);
workbook.worksheets.getItem("Prompt Examples").getRange("J2:J49").values = Array.from({ length: 48 }, () => ["APPROVED"]);
workbook.worksheets.getItem("Instructions").getRange("A1").values = [["Pilot v3 wording approval recorded"]];
workbook.worksheets.getItem("Instructions").getRange("B4:B11").values = [
  ["Measurement design approved. Primary activation remains the final user-question token before any answer."],
  ["All 30 Topic Candidates are approved for wording and matched-pair clarity."],
  ["Wording approval does not replace factual source verification; source_status remains PENDING."],
  ["All six Condition Wording templates are approved."],
  ["All 48 representative Prompt Examples are approved."],
  ["Next: verify each proposition using reliable sources and record source URLs."],
  ["After verification: resolve ambiguity, freeze wording, then assign hidden splits."],
  ["Full generation, activations, and probe training remain pending until those controls are complete."],
];

for (const [sheet, range] of [
  ["Summary", "A1:F16"], ["Measurement Design", "A1:F8"],
  ["Topic Candidates", "A1:G31"], ["Condition Wording", "A1:I7"],
  ["Prompt Examples", "A1:K49"],
]) {
  const result = await workbook.inspect({ kind: "table", sheetId: sheet, range, include: "values,formulas", tableMaxRows: 8, tableMaxCols: 12, maxChars: 3000 });
  console.log(result.ndjson);
}
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });
console.log(errors.ndjson);

await fs.mkdir(renderDir, { recursive: true });
for (const [sheet, range, filename] of [
  ["Summary", "A1:F16", "summary.png"], ["Measurement Design", "A1:F8", "measurement.png"],
  ["Topic Candidates", "A1:G31", "topics.png"], ["Condition Wording", "A1:I7", "conditions.png"],
  ["Prompt Examples", "A1:K49", "examples.png"], ["Instructions", "A1:B11", "instructions.png"],
]) {
  const preview = await workbook.render({ sheetName: sheet, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(renderDir, filename), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);

const design = JSON.parse(await fs.readFile(jsonPath, "utf8"));
design.status = "researcher_wording_approved";
design.wording_approved_on = "2026-08-19";
design.wording_approval_scope = "measurement design, all 30 topic pairs, all 6 conditions, and all 48 representative prompt examples";
for (const topic of design.topics) topic.researcher_decision = "APPROVED";
for (const condition of design.conditions) condition.researcher_decision = "APPROVED";
await fs.writeFile(jsonPath, `${JSON.stringify(design, null, 2)}\n`, "utf8");

console.log(`Approved workbook saved: ${workbookPath}`);
