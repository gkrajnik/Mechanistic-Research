import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourceDir = "inputs/draft/stage2d_by_topic";
const outputDir = "inputs/draft/stage3_assigned_by_topic";
const splitPath = "inputs/validated/stage3_split_assignment_v1.json";
const reviewPath = "inputs/draft/stage3_split_review.xlsx";
const renderDir = "tests/stage3_split_review_renders";

const assignment = JSON.parse(await fs.readFile(splitPath, "utf8"));
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(renderDir, { recursive: true });

const csvCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const toCsv = (rows) => rows.map((row) => row.map(csvCell).join(",")).join("\n") + "\n";

const assignedRows = [];
const topicMapRows = [["pair_id", "topic", "topic_split", "row_count", "unique_split_count"]];

for (const pairId of Object.keys(assignment.topic_assignments).sort()) {
  const csvText = await fs.readFile(path.join(sourceDir, `${pairId}.csv`), "utf8");
  const imported = await Workbook.fromCSV(csvText, { sheetName: "Data" });
  const values = imported.worksheets.getItem("Data").getUsedRange().values;
  const sourceHeaders = values[0].map(String);
  const sourceRows = values.slice(1);
  const splitIndex = sourceHeaders.indexOf("split");
  const familyIndex = sourceHeaders.indexOf("template_family");
  const topicIndex = sourceHeaders.indexOf("topic");
  if (splitIndex < 0 || familyIndex < 0 || topicIndex < 0) {
    throw new Error(`Required column missing from ${pairId}.csv`);
  }

  const topicSplit = assignment.topic_assignments[pairId];
  const outputHeaders = [
    ...sourceHeaders.slice(0, splitIndex + 1),
    "topic_split",
    "template_partition",
    ...sourceHeaders.slice(splitIndex + 1),
  ];
  const outputRows = sourceRows.map((sourceRow) => {
    const row = [...sourceRow];
    row[splitIndex] = topicSplit;
    const family = String(row[familyIndex]);
    const templatePartition = assignment.template_partitions[family];
    if (!templatePartition) throw new Error(`No template partition for ${family}`);
    return [
      ...row.slice(0, splitIndex + 1),
      topicSplit,
      templatePartition,
      ...row.slice(splitIndex + 1),
    ];
  });

  await fs.writeFile(
    path.join(outputDir, `${pairId}.csv`),
    toCsv([outputHeaders, ...outputRows]),
    "utf8",
  );
  assignedRows.push(...outputRows);
  topicMapRows.push([
    pairId,
    String(sourceRows[0][topicIndex]),
    topicSplit,
    outputRows.length,
    1,
  ]);
}

const headers = [
  "example_id", "pair_id", "topic", "split", "topic_split", "template_partition",
  "frame", "factuality", "template_family", "instruction_template_id",
  "question_variant", "context", "question", "answer_format", "forced_answer",
  "factual_answer", "source_note", "review_status",
];
const index = Object.fromEntries(headers.map((name, i) => [name, i]));
const count = (conditions) => assignedRows.filter((row) => Object.entries(conditions)
  .every(([column, value]) => String(row[index[column]]) === value)).length;

const uniqueIds = new Set(assignedRows.map((row) => String(row[index.example_id])));
const pairSplits = new Map();
for (const row of assignedRows) {
  const pair = String(row[index.pair_id]);
  if (!pairSplits.has(pair)) pairSplits.set(pair, new Set());
  pairSplits.get(pair).add(String(row[index.topic_split]));
}
const leakagePairs = [...pairSplits.values()].filter((splits) => splits.size > 1).length;

const metrics = [
  ["Total assigned rows", 480, assignedRows.length],
  ["Unique example IDs", 480, uniqueIds.size],
  ["Topic files", 10, topicMapRows.length - 1],
  ["Pair IDs crossing topic splits", 0, leakagePairs],
  ["Train topic rows", 288, count({ topic_split: "train" })],
  ["Validation topic rows", 96, count({ topic_split: "validation" })],
  ["Test topic rows", 96, count({ topic_split: "test" })],
  ["Development-template rows", 400, count({ template_partition: "development" })],
  ["Held-out-wording rows", 80, count({ template_partition: "heldout_wording" })],
  ["Probe-fitting subset", 240, count({ topic_split: "train", template_partition: "development" })],
  ["Layer/threshold validation", 80, count({ topic_split: "validation", template_partition: "development" })],
  ["Primary held-out-topic test", 80, count({ topic_split: "test", template_partition: "development" })],
  ["Held-out-wording test", 48, count({ topic_split: "train", template_partition: "heldout_wording" })],
  ["Joint generalization test", 16, count({ topic_split: "test", template_partition: "heldout_wording" })],
  ["Descriptive validation wording", 16, count({ topic_split: "validation", template_partition: "heldout_wording" })],
];
for (const [name, expected, observed] of metrics) {
  if (expected !== observed) throw new Error(`${name}: expected ${expected}; observed ${observed}`);
}
if (count({ template_family: "F06", template_partition: "development" }) !== 0) {
  throw new Error("F06 leaked into the development partition");
}
for (const family of ["F01", "F02", "F03", "F04", "F05"]) {
  if (count({ template_family: family, template_partition: "heldout_wording" }) !== 0) {
    throw new Error(`${family} leaked into held-out wording`);
  }
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const topicMap = workbook.worksheets.add("Topic Map");
const subsetMap = workbook.worksheets.add("Subset Rules");
const guide = workbook.worksheets.add("Guide");

summary.showGridLines = false;
summary.getRange("A1:D1").merge();
summary.getRange("A1").values = [["Stage 3 Split Assignment Review"]];
summary.getRange("A1:D1").format = {
  fill: "#1F4E78",
  font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" },
};
summary.getRange("A3:D18").values = [
  ["Check", "Expected", "Observed", "Status"],
  ...metrics.map(([name, expected, observed]) => [
    name, expected, observed, expected === observed ? "PASS" : "CHECK",
  ]),
];
summary.getRange("A3:D3").format = {
  fill: "#D9EAF7",
  font: { bold: true, color: "#163A5C" },
  borders: { preset: "bottom", style: "medium", color: "#7AA6C2" },
};
summary.getRange("A1:D18").format.font = { name: "Aptos", size: 10 };
summary.getRange("B4:D18").format.horizontalAlignment = "center";
summary.getRange("B4:C18").format.numberFormat = "0";
summary.getRange("A1:A18").format.columnWidth = 34;
summary.getRange("B1:D18").format.columnWidth = 14;
summary.freezePanes.freezeRows(3);

topicMap.showGridLines = false;
topicMap.getRange("A1:E11").values = topicMapRows;
topicMap.getRange("A1:E1").format = {
  fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" },
};
topicMap.tables.add("A1:E11", true, "Stage3TopicMapTable").style = "TableStyleMedium2";
topicMap.freezePanes.freezeRows(1);
topicMap.getRange("A1:E11").format.font = { name: "Aptos", size: 10 };
topicMap.getRange("A1:A11").format.columnWidth = 12;
topicMap.getRange("B1:B11").format.columnWidth = 26;
topicMap.getRange("C1:E11").format.columnWidth = 18;
topicMap.getRange("A2:E11").format.horizontalAlignment = "center";

const ruleRows = [
  ["Subset", "topic_split", "template_partition", "rows", "permitted_use"],
  ["Probe fitting", "train", "development", 240, "Fit probe coefficients only"],
  ["Layer/threshold validation", "validation", "development", 80, "Select shared layer and thresholds"],
  ["Primary topic test", "test", "development", 80, "Final new-topic evaluation"],
  ["Held-out wording test", "train", "heldout_wording", 48, "Evaluate unseen wording on familiar facts"],
  ["Joint generalization", "test", "heldout_wording", 16, "Evaluate unseen topics and wording"],
  ["Descriptive validation wording", "validation", "heldout_wording", 16, "Report only; never tune"],
];
subsetMap.showGridLines = false;
subsetMap.getRange("A1:E7").values = ruleRows;
subsetMap.getRange("A1:E1").format = {
  fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, wrapText: true,
};
subsetMap.tables.add("A1:E7", true, "Stage3SubsetRulesTable").style = "TableStyleMedium2";
subsetMap.freezePanes.freezeRows(1);
subsetMap.getRange("A1:E7").format.font = { name: "Aptos", size: 10 };
subsetMap.getRange("A1:A7").format.columnWidth = 28;
subsetMap.getRange("B1:C7").format.columnWidth = 20;
subsetMap.getRange("D1:D7").format.columnWidth = 12;
subsetMap.getRange("E1:E7").format.columnWidth = 42;
subsetMap.getRange("E2:E7").format.wrapText = true;
subsetMap.getRange("A2:D7").format.horizontalAlignment = "center";
subsetMap.getRange("A2:E7").format.rowHeight = 30;

guide.showGridLines = false;
guide.getRange("A1:D1").merge();
guide.getRange("A1").values = [["Stage 3 Assignment Guide"]];
guide.getRange("A1:D1").format = {
  fill: "#1F4E78",
  font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" },
};
guide.getRange("A3:B10").values = [
  ["Item", "Meaning"],
  ["Source preservation", "Stage 2D topic files remain unchanged."],
  ["Working copies", "Assigned rows are stored separately under stage3_assigned_by_topic."],
  ["Topic split", "Every pair_id belongs to exactly one train, validation, or test split."],
  ["Wording holdout", "Both N06 and R06 are evaluation-only and never used for fitting or selection."],
  ["Current status", "Split assigned; dataset facts and wording are not yet Stage 4 validated."],
  ["Next gate", "Run automated schema/balance checks and complete manual fact review."],
  ["No model run", "No activations, probes, or generated answers have been produced."],
];
guide.getRange("A3:B3").format = {
  fill: "#D9EAF7", font: { bold: true, color: "#163A5C" },
};
guide.getRange("A1:B10").format.font = { name: "Aptos", size: 10 };
guide.getRange("A1:A10").format.columnWidth = 24;
guide.getRange("B1:B10").format.columnWidth = 72;
guide.getRange("B4:B10").format.wrapText = true;
guide.getRange("A4:B10").format.rowHeight = 32;

const inspect = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:D18",
  include: "values,formulas",
  tableMaxRows: 18,
  tableMaxCols: 4,
});
console.log(inspect.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

for (const [sheetName, range, fileName] of [
  ["Summary", "A1:D18", "summary.png"],
  ["Topic Map", "A1:E11", "topic_map.png"],
  ["Subset Rules", "A1:E7", "subset_rules.png"],
  ["Guide", "A1:D10", "guide.png"],
]) {
  const render = await workbook.render({ sheetName, range, scale: 1.5, format: "png" });
  await fs.writeFile(path.join(renderDir, fileName), new Uint8Array(await render.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(reviewPath);
console.log(JSON.stringify({ assignedRows: assignedRows.length, leakagePairs, reviewPath }));
