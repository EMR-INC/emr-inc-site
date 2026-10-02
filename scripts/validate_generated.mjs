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

for (const match of page.matchAll(/<script[^>]*src="([^"\s]+)"[^>]*>/g)) {
  if (/^https?:\/\//.test(match[1])) continue;
  const file = match[1].replace(/^\//, "");
  // Vercel serves this Analytics asset dynamically from the deployed project.
  if (file === "_vercel/insights/script.js") continue;
  new vm.Script(fs.readFileSync(file, "utf8"), { filename: file });
}

if (page.includes('id="rescue-one"')) {
  const rescue = JSON.parse(fs.readFileSync("assets/rescue-one/counts.json", "utf8"));
  function onlyKeys(value, keys) {
    if (!value || typeof value !== "object" || Object.keys(value).some(key => !keys.includes(key))) {
      throw new Error("Unexpected field in public Rescue 1 aggregate");
    }
  }
  onlyKeys(rescue, ["window", "streams"]);
  onlyKeys(rescue.window, ["start", "end"]);
  onlyKeys(rescue.streams, ["sarasota", "charlotte"]);
  for (const name of ["sarasota", "charlotte"]) {
    const stream = rescue.streams[name];
    onlyKeys(stream, ["total", "daily"]);
    if (!Number.isInteger(stream.total) || stream.total < 0 || stream.daily?.length !== 8) {
      throw new Error("Invalid public Rescue 1 daily series");
    }
    stream.daily.forEach(day => {
      onlyKeys(day, ["date", "count", "partial"]);
      if (!Number.isInteger(day.count) || day.count < 0 || typeof day.partial !== "boolean") {
        throw new Error("Invalid public Rescue 1 daily count");
      }
    });
    if (stream.daily.reduce((sum, day) => sum + day.count, 0) !== stream.total) {
      throw new Error("Public Rescue 1 counts do not reconcile");
    }
  }
}

const embedded = page.match(/<script id="report_data" type="application\/json">([\s\S]*?)<\/script>/);
if (!embedded) throw new Error("Embedded report snapshot is missing");
const embeddedData = JSON.parse(embedded[1]);
if (embeddedData.generated_at_utc !== data.generated_at_utc) {
  throw new Error("Open-data page and research snapshot are out of sync");
}

console.log("Generated research and open-data artifacts are valid");
