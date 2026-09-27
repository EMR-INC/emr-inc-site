import fs from "node:fs";
import vm from "node:vm";

const page = fs.readFileSync("open-data.html", "utf8");
const source = fs.readFileSync("research.html", "utf8");
const data = JSON.parse(fs.readFileSync("data/research.json", "utf8"));

if (!page.includes("HOW THE<br>NUMBER") || !page.includes("HOLDS.")) {
  throw new Error("Approved split-display title is missing");
}
if (!source.includes(String(data.metrics.total_alert_candidates))) {
  throw new Error("research.html does not contain the current total");
}
if (page.includes("__RESEARCH_DATA_JSON__")) {
  throw new Error("Open-data template placeholder reached production output");
}

for (const match of page.matchAll(/<script(?![^>]*type="application\/json")[^>]*>([\s\S]*?)<\/script>/g)) {
  new vm.Script(match[1], { filename: "open-data.html" });
}

const embedded = page.match(/<script id="report_data" type="application\/json">([\s\S]*?)<\/script>/);
if (!embedded) throw new Error("Embedded report snapshot is missing");
const embeddedData = JSON.parse(embedded[1]);
if (embeddedData.generated_at_utc !== data.generated_at_utc) {
  throw new Error("Open-data page and research snapshot are out of sync");
}

console.log("Generated research and open-data artifacts are valid");
