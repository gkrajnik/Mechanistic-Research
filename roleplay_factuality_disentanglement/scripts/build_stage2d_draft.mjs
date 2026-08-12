import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const specPath = "inputs/draft/stage2d_dataset_spec.json";
const topicDir = "inputs/draft/stage2d_by_topic";
const manifestPath = "inputs/draft/stage2d_manifest.csv";
const workbookPath = "inputs/draft/stage2d_review.xlsx";
const renderDir = "tests/stage2d_review_renders";

const spec = JSON.parse(await fs.readFile(specPath, "utf8"));
await fs.mkdir(topicDir, { recursive: true });
await fs.mkdir(renderDir, { recursive: true });

const headers = [
  "example_id", "pair_id", "topic", "split", "frame", "factuality",
  "template_family", "instruction_template_id", "question_variant", "context",
  "question", "answer_format", "forced_answer", "factual_answer", "source_note",
  "review_status",
];

const csvCell = (value) => `"${String(value).replaceAll('"', '""')}"`;
const toCsv = (rows) => [headers, ...rows]
  .map((row) => row.map(csvCell).join(","))
  .join("\n") + "\n";

const allRows = [];
const manifest = [];

for (let topicIndex = 0; topicIndex < spec.topics.length; topicIndex += 1) {
  const topic = spec.topics[topicIndex];
  const scenario = spec.neutral_scenarios[topicIndex % spec.neutral_scenarios.length];
  const topicRows = [];
  let localIndex = 1;
  const questions = [
    {
      variant: "true_form",
      question: topic.true_question,
      factualAnswer: "Yes",
      sourceNote: topic.true_source_note,
    },
    {
      variant: "false_form",
      question: topic.false_question,
      factualAnswer: "No",
      sourceNote: topic.false_source_note,
    },
  ];

  for (const question of questions) {
    for (const pair of spec.template_pairs) {
      const frames = [
        ["normal", pair.normal_id, pair.normal_context],
        ["roleplay", pair.roleplay_id, pair.roleplay_context],
      ];
      for (const [frame, templateId, rawContext] of frames) {
        const context = rawContext.replace("{short_scenario}", scenario);
        for (const forcedAnswer of ["Yes", "No"]) {
          const factuality = forcedAnswer === question.factualAnswer
            ? "factual"
            : "nonfactual";
          const row = [
            `D_${topic.pair_id}_${String(localIndex).padStart(3, "0")}`,
            topic.pair_id,
            topic.topic,
            "unassigned",
            frame,
            factuality,
            pair.family,
            templateId,
            question.variant,
            context,
            question.question,
            spec.answer_format,
            forcedAnswer,
            question.factualAnswer,
            question.sourceNote,
            "draft",
          ];
          topicRows.push(row);
          allRows.push(row);
          localIndex += 1;
        }
      }
    }
  }

  const index = Object.fromEntries(headers.map((name, column) => [name, column]));
  const count = (column, value) => topicRows.filter((row) => row[index[column]] === value).length;
  const unique = (column) => new Set(topicRows.map((row) => row[index[column]])).size;
  manifest.push([
    topic.pair_id,
    topic.topic,
    topicRows.length,
    count("frame", "normal"),
    count("frame", "roleplay"),
    count("factuality", "factual"),
    count("factuality", "nonfactual"),
    count("forced_answer", "Yes"),
    count("forced_answer", "No"),
    count("factual_answer", "Yes"),
    count("factual_answer", "No"),
    unique("instruction_template_id"),
    unique("question_variant"),
    "draft_unvalidated",
  ]);

  await fs.writeFile(
    path.join(topicDir, `${topic.pair_id}.csv`),
    toCsv(topicRows),
    "utf8",
  );
}

const manifestHeaders = [
  "pair_id", "topic", "total_rows", "normal_rows", "roleplay_rows",
  "factual_rows", "nonfactual_rows", "forced_yes", "forced_no",
  "factual_answer_yes", "factual_answer_no", "template_ids", "question_forms",
  "status",
];
const manifestCsv = [manifestHeaders, ...manifest]
  .map((row) => row.map(csvCell).join(","))
  .join("\n") + "\n";
await fs.writeFile(manifestPath, manifestCsv, "utf8");

// Structural assertions fail the build before any review workbook is exported.
const ids = allRows.map((row) => row[0]);
if (allRows.length !== 480) throw new Error(`Expected 480 rows; received ${allRows.length}`);
if (new Set(ids).size !== ids.length) throw new Error("Duplicate example_id values found");
for (const row of manifest) {
  const counts = row.slice(2, 11);
  const expected = [48, 24, 24, 24, 24, 24, 24, 24, 24];
  if (counts.some((value, i) => value !== expected[i])) {
    throw new Error(`Balance failure for ${row[0]}: ${counts.join(",")}`);
  }
  if (row[11] !== 12 || row[12] !== 2) {
    throw new Error(`Coverage failure for ${row[0]}`);
  }
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const topicSheet = workbook.worksheets.add("Topic Manifest");
const templateSheet = workbook.worksheets.add("Template Manifest");
const guide = workbook.worksheets.add("Guide");

summary.showGridLines = false;
summary.getRange("A1:D1").merge();
summary.getRange("A1").values = [["Stage 2D Full Draft Balance Review"]];
summary.getRange("A1:D1").format = {
  fill: "#1F4E78",
  font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
};
summary.getRange("A1:D1").format.rowHeight = 34;
summary.getRange("A3:D14").values = [
  ["Check", "Expected", "Observed", "Status"],
  ["Total rows", 480, null, null],
  ["Topic files", 10, null, null],
  ["Rows per topic", 48, null, null],
  ["Normal frame", 240, null, null],
  ["Role-play frame", 240, null, null],
  ["Factual rows", 240, null, null],
  ["Nonfactual rows", 240, null, null],
  ["Forced Yes", 240, null, null],
  ["Forced No", 240, null, null],
  ["Factual answer Yes", 240, null, null],
  ["Factual answer No", 240, null, null],
];
summary.getRange("C4:C14").formulas = [
  ["=SUM('Topic Manifest'!C2:C11)"],
  ["=COUNTA('Topic Manifest'!A2:A11)"],
  ["=MIN('Topic Manifest'!C2:C11)"],
  ["=SUM('Topic Manifest'!D2:D11)"],
  ["=SUM('Topic Manifest'!E2:E11)"],
  ["=SUM('Topic Manifest'!F2:F11)"],
  ["=SUM('Topic Manifest'!G2:G11)"],
  ["=SUM('Topic Manifest'!H2:H11)"],
  ["=SUM('Topic Manifest'!I2:I11)"],
  ["=SUM('Topic Manifest'!J2:J11)"],
  ["=SUM('Topic Manifest'!K2:K11)"],
];
summary.getRange("D4:D14").formulas = Array.from({ length: 11 }, (_, i) => [
  `=IF(B${i + 4}=C${i + 4},"PASS","CHECK")`,
]);
summary.getRange("A3:D3").format = {
  fill: "#D9EAF7",
  font: { bold: true, color: "#163A5C" },
  borders: { preset: "bottom", style: "medium", color: "#7AA6C2" },
};
summary.getRange("A3:D14").format.font = { name: "Aptos", size: 10 };
summary.getRange("B4:C14").format.numberFormat = "0";
summary.getRange("B3:D14").format.horizontalAlignment = "center";
summary.getRange("A1:A14").format.columnWidth = 28;
summary.getRange("B1:D14").format.columnWidth = 14;
summary.freezePanes.freezeRows(3);

topicSheet.showGridLines = false;
topicSheet.getRange("A1:N11").values = [manifestHeaders, ...manifest];
topicSheet.getRange("A1:N1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
};
topicSheet.tables.add("A1:N11", true, "TopicManifestTable").style = "TableStyleMedium2";
topicSheet.freezePanes.freezeRows(1);
topicSheet.getRange("A1:N11").format.font = { name: "Aptos", size: 10 };
topicSheet.getRange("A1:A11").format.columnWidth = 10;
topicSheet.getRange("B1:B11").format.columnWidth = 24;
topicSheet.getRange("C1:M11").format.columnWidth = 15;
topicSheet.getRange("N1:N11").format.columnWidth = 20;

const templateRows = [["family", "frame", "template_id", "context"]];
for (const pair of spec.template_pairs) {
  templateRows.push([pair.family, "normal", pair.normal_id, pair.normal_context]);
  templateRows.push([pair.family, "roleplay", pair.roleplay_id, pair.roleplay_context]);
}
templateSheet.showGridLines = false;
templateSheet.getRange("A1:D13").values = templateRows;
templateSheet.getRange("A1:D1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
};
templateSheet.tables.add("A1:D13", true, "TemplateManifestTable").style = "TableStyleMedium2";
templateSheet.freezePanes.freezeRows(1);
templateSheet.getRange("A1:C13").format.columnWidth = 14;
templateSheet.getRange("D1:D13").format.columnWidth = 70;
templateSheet.getRange("D2:D13").format.wrapText = true;
templateSheet.getRange("A1:D13").format.font = { name: "Aptos", size: 10 };
templateSheet.getRange("A2:C13").format.horizontalAlignment = "center";
templateSheet.getRange("A2:D13").format.rowHeight = 34;

guide.showGridLines = false;
guide.getRange("A1:D1").merge();
guide.getRange("A1").values = [["Stage 2D Draft Guide"]];
guide.getRange("A1:D1").format = {
  fill: "#1F4E78",
  font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" },
};
guide.getRange("A3:B10").values = [
  ["Item", "Meaning"],
  ["Status", "Draft and structurally checked; not fact-validated or split."],
  ["Storage", "Ten topic CSV files with 48 rows each."],
  ["Factorial cells", "Normal factual, normal nonfactual, role-play factual, role-play nonfactual."],
  ["Question forms", "One factual-answer-Yes and one factual-answer-No question per topic."],
  ["Forced answers", "Both Yes and No are evaluated for every question and frame."],
  ["Next gate", "Manual wording review before Stage 3 split assignment."],
  ["No model run", "No activations or generated answers are included."],
];
guide.getRange("A3:B3").format = {
  fill: "#D9EAF7",
  font: { bold: true, color: "#163A5C" },
};
guide.getRange("A1:B10").format.font = { name: "Aptos", size: 10 };
guide.getRange("A1:A10").format.columnWidth = 22;
guide.getRange("B1:B10").format.columnWidth = 70;
guide.getRange("B4:B10").format.wrapText = true;
guide.getRange("A4:B10").format.rowHeight = 32;

const check = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:D14",
  include: "values,formulas",
  tableMaxRows: 14,
  tableMaxCols: 4,
});
console.log(check.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

for (const [sheetName, range, fileName] of [
  ["Summary", "A1:D14", "summary.png"],
  ["Topic Manifest", "A1:N11", "topic_manifest.png"],
  ["Template Manifest", "A1:D13", "template_manifest.png"],
  ["Guide", "A1:D10", "guide.png"],
]) {
  const render = await workbook.render({ sheetName, range, scale: 1.5, format: "png" });
  await fs.writeFile(path.join(renderDir, fileName), new Uint8Array(await render.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(workbookPath);

console.log(JSON.stringify({
  rows: allRows.length,
  topicFiles: manifest.length,
  workbookPath,
}));
