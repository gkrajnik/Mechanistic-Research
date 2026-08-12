import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const csvPath = "inputs/draft/stage2c_two_topic_preview.csv";
const xlsxPath = "inputs/draft/stage2c_two_topic_preview.xlsx";
const renderPath = "tests/stage2c_preview_render.png";

const csvText = await fs.readFile(csvPath, "utf8");
const workbook = await Workbook.fromCSV(csvText, { sheetName: "Preview Data" });
const data = workbook.worksheets.getItem("Preview Data");
data.showGridLines = false;
data.freezePanes.freezeRows(1);
data.getRange("A1:M33").format = {
  font: { name: "Aptos", size: 10, color: "#1F2937" },
  verticalAlignment: "top",
};
data.getRange("A1:M1").format = {
  fill: "#1F4E78",
  font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#163A5C" },
};
data.getRange("A1:M1").format.rowHeight = 30;
data.getRange("A2:M33").format.rowHeight = 30;
data.getRange("D2:G33").format.horizontalAlignment = "center";
data.getRange("J2:M33").format.horizontalAlignment = "center";
data.getRange("H2:I33").format.wrapText = true;
data.getRange("L2:L33").format.wrapText = true;

const widths = {
  A: 12, B: 9, C: 13, D: 12, E: 11, F: 12, G: 20,
  H: 58, I: 35, J: 14, K: 14, L: 42, M: 13,
};
for (const [column, width] of Object.entries(widths)) {
  data.getRange(`${column}1:${column}33`).format.columnWidth = width;
}
data.tables.add("A1:M33", true, "Stage2CPreviewTable").style = "TableStyleMedium2";

const qc = workbook.worksheets.add("Balance Check");
qc.showGridLines = false;
qc.getRange("A1:C1").merge();
qc.getRange("A1").values = [["Stage 2C Preview Quality Check"]];
qc.getRange("A1:C1").format = {
  fill: "#1F4E78",
  font: { name: "Aptos Display", size: 16, bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
};
qc.getRange("A1:C1").format.rowHeight = 34;
qc.getRange("A3:C12").values = [
  ["Check", "Expected", "Observed"],
  ["Total rows", 32, null],
  ["Normal frame", 16, null],
  ["Role-play frame", 16, null],
  ["Factual rows", 16, null],
  ["Nonfactual rows", 16, null],
  ["Forced Yes", 16, null],
  ["Forced No", 16, null],
  ["Factual answer Yes", 16, null],
  ["Factual answer No", 16, null],
];
qc.getRange("C4:C12").formulas = [
  ["=COUNTA('Preview Data'!A2:A33)"],
  ["=COUNTIF('Preview Data'!E2:E33,\"normal\")"],
  ["=COUNTIF('Preview Data'!E2:E33,\"roleplay\")"],
  ["=COUNTIF('Preview Data'!F2:F33,\"factual\")"],
  ["=COUNTIF('Preview Data'!F2:F33,\"nonfactual\")"],
  ["=COUNTIF('Preview Data'!J2:J33,\"Yes\")"],
  ["=COUNTIF('Preview Data'!J2:J33,\"No\")"],
  ["=COUNTIF('Preview Data'!K2:K33,\"Yes\")"],
  ["=COUNTIF('Preview Data'!K2:K33,\"No\")"],
];
qc.getRange("A3:C3").format = {
  fill: "#D9EAF7",
  font: { name: "Aptos", size: 10, bold: true, color: "#163A5C" },
  borders: { preset: "bottom", style: "medium", color: "#7AA6C2" },
};
qc.getRange("A4:C12").format = {
  font: { name: "Aptos", size: 10, color: "#1F2937" },
};
qc.getRange("B4:C12").format.numberFormat = "0";
qc.getRange("A1:A12").format.columnWidth = 28;
qc.getRange("B1:C12").format.columnWidth = 14;
qc.getRange("B3:C12").format.horizontalAlignment = "center";
qc.freezePanes.freezeRows(3);

const check = await workbook.inspect({
  kind: "table",
  range: "Balance Check!A1:C12",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 3,
});
console.log(check.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "Balance Check",
  range: "A1:C12",
  scale: 2,
  format: "png",
});
await fs.writeFile(renderPath, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(xlsxPath);
