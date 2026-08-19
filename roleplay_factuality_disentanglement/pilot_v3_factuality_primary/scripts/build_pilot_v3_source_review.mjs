import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
const designPath = path.join(projectRoot, "inputs", "draft", "wording_review", "pilot_v3_design_draft.json");
const outputDir = path.join(projectRoot, "inputs", "draft", "source_review");
const renderDir = path.join(projectRoot, "tests", "source_review_renders");
const workbookPath = path.join(outputDir, "PILOT_V3_SOURCE_REVIEW.xlsx");
const jsonPath = path.join(outputDir, "pilot_v3_source_review.json");

const design = JSON.parse(await fs.readFile(designPath, "utf8"));
const evidence = [
  ["V3T01", "VERIFIED", "NASA reports the Moon's orbital distance relative to the body it orbits, Earth.", "https://science.nasa.gov/moon/by-the-numbers/", "NASA", "NONE"],
  ["V3T02", "VERIFIED", "NASA identifies Jupiter as the largest planet in the Solar System.", "https://science.nasa.gov/solar-system/planet-sizes-and-locations-in-our-solar-system/", "NASA", "NONE"],
  ["V3T03", "VERIFIED", "NIST identifies sodium chloride and lists salt as another name; its safety sheet also lists table salt.", "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7647145&Mask=25AF&Units=CAL", "NIST", "NONE"],
  ["V3T04", "VERIFIED", "NIST's atomic-number table lists oxygen as element 8.", "https://physics.nist.gov/PhysRefData/Handbook/atomic_number_a.htm", "NIST", "NONE"],
  ["V3T05", "VERIFIED", "Smithsonian describes bats as mammals and notes their mammalian characteristics.", "https://www.si.edu/spotlight/bats/batfacts", "Smithsonian Institution", "NONE"],
  ["V3T06", "VERIFIED", "Smithsonian explains that cephalopods, including octopuses, have three hearts.", "https://ocean.si.edu/ocean-life/invertebrates/octopuses-squids-and-relatives", "Smithsonian Ocean", "NONE"],
  ["V3T07", "VERIFIED", "NIDDK states that the liver makes bile.", "https://www.niddk.nih.gov/health-information/digestive-diseases/digestive-system-how-it-works", "NIH/NIDDK", "NONE"],
  ["V3T08", "VERIFIED", "NHLBI states that arteries take blood away from the heart.", "https://www.nhlbi.nih.gov/health/heart/blood-flow", "NIH/NHLBI", "QUALIFIER_RETAINED"],
  ["V3T09", "VERIFIED", "MathWorld defines a regular hexagon as a regular polygon with six sides.", "https://mathworld.wolfram.com/RegularHexagon.html", "Wolfram MathWorld", "NONE"],
  ["V3T10", "VERIFIED", "The government-supported NZ Maths resource explicitly gives square root of 64 as 8.", "https://meaningfulmaths.nt.edu.au/mmws/nz/resource/square-and-cube-roots.html", "NZ Maths / Northern Territory Education", "NONE"],
  ["V3T11", "VERIFIED", "The OAS describes the Amazon River Basin as lying in South America.", "https://www.oas.org/dsd/Events/english/Documents/OSDE_8Amazon.pdf", "Organization of American States", "NONE"],
  ["V3T12", "VERIFIED", "The Government of Japan lists Tokyo as Japan's capital.", "https://www.japan.go.jp/japan/index.html", "Government of Japan", "NONE"],
  ["V3T13", "VERIFIED", "The Morgan Library identifies Pride and Prejudice as Austen's novel and documents its 1813 edition.", "https://www.themorgan.org/exhibitions/online/jane-austen/6", "Morgan Library & Museum", "NONE"],
  ["V3T14", "VERIFIED", "Harvard's Center for Hellenic Studies discusses the traditional attribution of the Odyssey to Homer.", "https://www-current.chs.harvard.edu/the-greek-language-a-brief-history/", "Harvard Center for Hellenic Studies", "QUALIFIER_REQUIRED"],
  ["V3T15", "VERIFIED", "NCBI's Molecular Biology of the Cell describes mitochondria as energy-converting organelles producing most cellular ATP.", "https://www.ncbi.nlm.nih.gov/books/NBK21063/", "NCBI Bookshelf", "NONE"],
  ["V3T16", "VERIFIED", "NCBI identifies chloroplasts as the organelles responsible for photosynthesis.", "https://www.ncbi.nlm.nih.gov/books/NBK9905/", "NCBI Bookshelf", "NONE"],
  ["V3T17", "VERIFIED", "NASA directly compares light and sound and states that light travels much faster in air-scale examples.", "https://cosmicopia.gsfc.nasa.gov/qa_gp_ls.html", "NASA GSFC", "NONE"],
  ["V3T18", "VERIFIED", "NASA educational material states that water typically freezes at 0 degrees Celsius.", "https://mars.nasa.gov/education/modules/water_activity5.pdf", "NASA", "QUALIFIER_RETAINED"],
  ["V3T19", "VERIFIED", "NASA documents Apollo 11 as the first crewed lunar landing mission in July 1969.", "https://www.nasa.gov/mission/apollo-11/", "NASA", "NONE"],
  ["V3T20", "VERIFIED", "The U.S. National Archives timeline records Japan's 1945 surrender as ending World War II.", "https://www.archives.gov/research/military/ww2/philippine/timeline", "U.S. National Archives", "NONE"],
  ["V3T21", "VERIFIED", "NIST documents binary multiples as powers of two, supporting binary notation's base-two structure.", "https://pml.nist.gov/cuu/Units/binary.html", "NIST", "NONE"],
  ["V3T22", "VERIFIED", "IETF RFC 9110 defines HTTP as a protocol for interaction with and transfer of resource representations.", "https://www.ietf.org/rfc/rfc9110.html", "IETF", "NONE"],
  ["V3T23", "VERIFIED", "USGS lists basalt among common extrusive igneous rocks.", "https://www.usgs.gov/faqs/what-are-igneous-rocks", "U.S. Geological Survey", "NONE"],
  ["V3T24", "VERIFIED", "USGS states that Earth's outer core is entirely liquid.", "https://www.usgs.gov/faqs/are-tectonic-plates-floating-magma", "U.S. Geological Survey", "NONE"],
  ["V3T25", "VERIFIED", "NOAA identifies the Pacific as Earth's largest ocean basin and the Arctic as the smallest.", "https://oceanservice.noaa.gov/facts/biggestocean.html", "NOAA", "NONE"],
  ["V3T26", "VERIFIED", "National Geographic states that Africa is divided almost equally by the Equator.", "https://media.nationalgeographic.org/assets/reference/assets/africa-human-geography-1.pdf", "National Geographic Society", "NONE"],
  ["V3T27", "VERIFIED", "Instituto Cervantes describes Spanish as a Romance language inherited from Latin.", "https://cvc.cervantes.es/ensenanza/biblioteca_ele/sicele/sicele03/006_matiasmonheler.htm", "Instituto Cervantes", "NONE"],
  ["V3T28", "VERIFIED", "The Library of Congress controlled vocabulary classifies trumpet under brass instruments.", "https://www.loc.gov/standards/valuelist/marcmusperf.html", "Library of Congress", "NONE"],
  ["V3T29", "VERIFIED", "NIDDK states that insulin lowers elevated blood glucose levels.", "https://www.niddk.nih.gov/-/media/Files/Diabetes/Causes_of_Diabetes_508.pdf", "NIH/NIDDK", "QUALIFIER_RETAINED"],
  ["V3T30", "VERIFIED", "USDA explains that land plants absorb soil water through roots and osmosis.", "https://www.ars.usda.gov/ARSUserFiles/oc/aglab/projects/plantgrowth/aglabprojectplantgrowthandosmoticpotential.pdf", "USDA Agricultural Research Service", "QUALIFIER_RETAINED"],
];

const evidenceById = new Map(evidence.map(row => [row[0], row]));
const rows = design.topics.map(topic => {
  const ev = evidenceById.get(topic.pair_id);
  if (!ev) throw new Error(`Missing source evidence for ${topic.pair_id}`);
  return [topic.pair_id, topic.domain, topic.true_claim, topic.false_claim, ...ev.slice(1), "PENDING", ""];
});

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const review = workbook.worksheets.add("Source Review");
const ambiguity = workbook.worksheets.add("Ambiguity Notes");
const instructions = workbook.worksheets.add("Instructions");
for (const sheet of [summary, review, ambiguity, instructions]) sheet.showGridLines = false;

const navy = "#17365D", blue = "#D9EAF7", cyan = "#BFE3F2", green = "#E2F0D9", yellow = "#FFF2CC", gray = "#E7E6E6";
summary.getRange("A1:H1").merge(); summary.getRange("A1").values = [["Pilot v3 — Source Verification and Factual-Freeze Review"]];
summary.getRange("A2:H2").merge(); summary.getRange("A2").values = [["All 30 pairs have supporting evidence; researcher factual-freeze approval is still required before split assignment"]];
summary.getRange("A4:B9").values = [
  ["Metric", "Value"], ["Approved wording pairs", 30], ["Source-verified pairs", 30],
  ["Pairs requiring wording revision", 0], ["Pairs with retained qualifiers", 4], ["Current gate", "PENDING FACTUAL-FREEZE APPROVAL"],
];
summary.getRange("D4:H9").values = [
  ["Control", "Result", "Meaning", "Next action", "Status"],
  ["Source coverage", "30 / 30", "Every pair has an auditable URL", "Review evidence", "COMPLETE"],
  ["Truth consistency", "30 / 30", "Sources support true claim and contradict paired false claim", "Review pairing", "COMPLETE"],
  ["Ambiguity screen", "0 revisions", "No source conflict requires rewriting", "Review qualifiers", "COMPLETE"],
  ["Factual freeze", "Not yet", "Researcher has not frozen sourced claims", "Approve or revise", "PENDING"],
  ["Hidden splits", "Not assigned", "Prevents premature split leakage", "Wait for freeze", "PENDING"],
];

const headers = ["pair_id", "domain", "true_claim", "false_claim", "verification_status", "evidence_summary", "source_url", "source_organization", "ambiguity_flag", "researcher_decision", "researcher_comment"];
review.getRange("A1:K1").values = [headers]; review.getRange("A2:K31").values = rows;
review.getRange("J2:J31").dataValidation = { rule: { type: "list", values: ["PENDING", "APPROVED", "REVISE"] } };
review.getRange("J2:J31").conditionalFormats.add("containsText", { text: "APPROVED", format: { fill: green, font: { color: "#375623" } } });
review.getRange("J2:J31").conditionalFormats.add("containsText", { text: "REVISE", format: { fill: "#F4CCCC", font: { color: "#9C0006" } } });

ambiguity.getRange("A1:F1").values = [["pair_id", "flag", "protected_wording", "reason", "recommended_action", "researcher_decision"]];
ambiguity.getRange("A2:F5").values = [
  ["V3T08", "QUALIFIER_RETAINED", "generally", "Arteries are defined by direction away from the heart; oxygenation has exceptions.", "Keep wording unchanged.", "PENDING"],
  ["V3T14", "QUALIFIER_REQUIRED", "traditionally attributed", "Homeric authorship is a historical attribution, not a settled single-author fact.", "Keep wording unchanged.", "PENDING"],
  ["V3T29", "QUALIFIER_RETAINED", "generally", "Insulin lowers elevated glucose, while physiological context can affect measured response.", "Keep wording unchanged.", "PENDING"],
  ["V3T30", "QUALIFIER_RETAINED", "commonly", "Roots are the standard uptake organ, while unusual pathways/species should not make the claim absolute.", "Keep wording unchanged.", "PENDING"],
];
ambiguity.getRange("F2:F5").dataValidation = { rule: { type: "list", values: ["PENDING", "APPROVED", "REVISE"] } };

instructions.getRange("A1:B1").merge(); instructions.getRange("A1").values = [["How to review the Pilot v3 factual freeze"]];
instructions.getRange("A3:B9").values = [
  ["Step", "Action"],
  [1, "Review each Source Review row. Open the URL and confirm the evidence supports the true claim and rules out the paired false claim."],
  [2, "Check the four Ambiguity Notes. Their qualifiers are deliberate protections, not unresolved errors."],
  [3, "Set researcher_decision to APPROVED or REVISE for all 30 source rows."],
  [4, "Set the four ambiguity decisions to APPROVED or REVISE."],
  [5, "Use researcher_comment for any requested replacement source or wording change."],
  [6, "Stop after review. Hidden splits and full dataset generation remain prohibited until factual-freeze approval."],
];

for (const sheet of [summary, review, ambiguity, instructions]) {
  const used = sheet.getUsedRange(); used.format.font = { name: "Aptos", size: 10, color: "#334155" }; used.format.verticalAlignment = "center";
}
summary.getRange("A1:H1").format = { fill: navy, font: { name: "Aptos Display", size: 18, bold: true, color: "#FFFFFF" }, rowHeight: 30 };
summary.getRange("A2:H2").format = { fill: blue, font: { italic: true, color: "#355269" }, rowHeight: 24 };
summary.getRange("A4:B4").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } }; summary.getRange("D4:H4").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A5:B9").format.fill = blue; summary.getRange("D5:H9").format.fill = green; summary.getRange("B9").format.fill = yellow;
summary.getRange("A1:H16").format.wrapText = true; summary.getRange("A:A").format.columnWidth = 24; summary.getRange("B:B").format.columnWidth = 30;
summary.getRange("C:C").format.columnWidth = 3; summary.getRange("D:D").format.columnWidth = 23; summary.getRange("E:E").format.columnWidth = 18; summary.getRange("F:F").format.columnWidth = 35; summary.getRange("G:G").format.columnWidth = 22; summary.getRange("H:H").format.columnWidth = 16;

for (const sheet of [review, ambiguity]) {
  const used = sheet.getUsedRange(); used.format.wrapText = true; used.format.borders = { insideHorizontal: { style: "thin", color: "#67C5E8" } };
  used.getRow(0).format = { fill: navy, font: { bold: true, color: "#FFFFFF" }, rowHeight: 32 };
  sheet.freezePanes.freezeRows(1);
}
review.getRange("A2:I31").format.fill = cyan; review.getRange("J2:K31").format.fill = yellow;
for (const [col, width] of [["A:A",12],["B:B",15],["C:D",34],["E:E",17],["F:F",48],["G:G",58],["H:H",26],["I:I",22],["J:J",21],["K:K",32]]) review.getRange(col).format.columnWidth = width;
review.getRange("2:31").format.rowHeight = 58;
ambiguity.getRange("A2:E5").format.fill = gray; ambiguity.getRange("F2:F5").format.fill = yellow;
for (const [col, width] of [["A:A",13],["B:B",22],["C:C",22],["D:D",52],["E:E",30],["F:F",22]]) ambiguity.getRange(col).format.columnWidth = width;
ambiguity.getRange("2:5").format.rowHeight = 58;

instructions.getRange("A1:B1").format = { fill: navy, font: { name: "Aptos Display", size: 18, bold: true, color: "#FFFFFF" }, rowHeight: 30 };
instructions.getRange("A3:B3").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } }; instructions.getRange("A4:B9").format.fill = blue;
instructions.getRange("A:A").format.columnWidth = 12; instructions.getRange("B:B").format.columnWidth = 105; instructions.getRange("A3:B9").format.wrapText = true; instructions.getRange("4:9").format.rowHeight = 38;

await fs.mkdir(outputDir, { recursive: true }); await fs.mkdir(renderDir, { recursive: true });
const payload = { version: "pilot_v3_source_review_v1", status: "pending_researcher_factual_freeze", verified_on: "2026-08-19", rows: rows.map(r => Object.fromEntries(headers.map((h, i) => [h, r[i]]))) };
await fs.writeFile(jsonPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");

for (const [sheet, range, file] of [["Summary","A1:H9","summary.png"],["Source Review","A1:K16","sources_top.png"],["Source Review","A17:K31","sources_bottom.png"],["Ambiguity Notes","A1:F5","ambiguity.png"],["Instructions","A1:B9","instructions.png"]]) {
  const preview = await workbook.render({ sheetName: sheet, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(renderDir, file), new Uint8Array(await preview.arrayBuffer()));
}
const check = await workbook.inspect({ kind: "table", sheetId: "Source Review", range: "A1:K31", include: "values,formulas", tableMaxRows: 8, tableMaxCols: 11, maxChars: 4500 }); console.log(check.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" }); console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook); await output.save(workbookPath);
console.log(`Source-review workbook saved: ${workbookPath}`);
