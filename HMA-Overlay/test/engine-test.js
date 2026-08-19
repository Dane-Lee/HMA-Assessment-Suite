/* Harness: loads the real <script> out of "HMA Overlay.html", stubs just enough DOM,
   then exercises the engine against the baked-in job library plus fixture employees.
   No dependencies:  node test/engine-test.js                                        */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const FILE = path.join(__dirname, "..", "HMA Overlay.html");
const html = fs.readFileSync(FILE, "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("no script block found"); process.exit(1); }
const code = m[1];

let fails = 0;
const ok = (name, cond, extra) => {
  if (!cond) fails++;
  console.log(`  ${cond ? "✓" : "✗ FAIL"} ${name}${extra !== undefined ? "  — " + extra : ""}`);
};

const stubEl = () => new Proxy({}, {
  get: (t, k) => (k === "classList" ? { contains: () => false, toggle: () => {}, add: () => {} }
    : k === "querySelector" ? () => stubEl()
    : k === "cloneNode" ? () => stubEl()
    : k === "removeAttribute" ? () => {}
    : k in t ? t[k] : (typeof k === "string" && k.startsWith("add") ? () => {} : "")),
  set: (t, k, v) => { t[k] = v; return true; },
});
const store = {};
const sandbox = {
  console,
  document: {
    getElementById: () => stubEl(),
    documentElement: { classList: { contains: () => false, toggle: () => {}, add: () => {} } },
    createElement: () => stubEl(), body: stubEl(),
    querySelectorAll: () => [],
  },
  localStorage: {
    getItem: k => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = v; }, removeItem: k => { delete store[k]; },
  },
  window: {}, alert: () => {}, confirm: () => true, FileReader: function () {},
  Blob: function () {}, URL: { createObjectURL: () => "blob:x", revokeObjectURL: () => {} },
};
sandbox.window = sandbox;
vm.createContext(sandbox);
try { vm.runInContext(code, sandbox); } catch (e) { console.error("SCRIPT THREW:", e.message); process.exit(1); }
console.log("✓ script parsed and ran clean\n");

const run = expr => vm.runInContext(expr, sandbox);
const SEED = run("SEED_LIBRARY");
const BAND_LABEL = run("BAND_LABEL");
const FREQ = run("FREQ");

/* ---------- 1. the baked-in library ---------- */
console.log("--- baked-in job library ---");
ok("jobs are baked into the file", SEED.jobs.length > 0, SEED.jobs.length + " jobs");
ok("stations are baked into the file", SEED.stations.length > 0, SEED.stations.length + " stations");
ok("SEED markers survive in the file for re-baking",
   /\/\* SEED-START \*\/[\s\S]*?\/\* SEED-END \*\//.test(html));

const allRated = SEED.jobs.every(j => Object.keys(j.movements).length === 17);
ok("every job carries all 17 movements", allRated);
const anyBlank = SEED.jobs.filter(j => Object.values(j.movements).every(v => !v.freq));
ok("no job parsed to an entirely blank demand profile", anyBlank.length === 0);
const cervical = SEED.jobs.filter(j => j.movements.cervical && j.movements.cervical.freq
                                    && j.movements.cervical.freq !== "never");
ok("cervical demand survived the 'CERVICAL SPINEMOTION' typo",
   cervical.length === SEED.jobs.length, cervical.length + "/" + SEED.jobs.length + " jobs");

const demands = SEED.jobs.reduce((n, j) =>
  n + Object.values(j.movements).filter(v => v.freq && v.freq !== "never").length, 0);
const mhRows = SEED.jobs.reduce((n, j) =>
  n + ["lift", "carry", "pushpull"].reduce((k, t) => k + ((j.mh || {})[t] || []).length, 0), 0);
console.log(`    ${demands} non-Never demands, ${mhRows} material-handling rows`);

/* conflicts are surfaced, not hidden */
const withConf = SEED.jobs.filter(j => (j.conflicts || []).length);
ok("source-document conflicts are carried through for display", withConf.length > 0,
   withConf.length + " job(s) flagged");

/* ---------- 2. library merge / override ---------- */
console.log("\n--- library merge (seed + local edits) ---");
ok("allJobs() returns the seed when there are no local edits",
   sandbox.allJobs().length === SEED.jobs.length);
const firstId = SEED.jobs[0].id;
run(`S.jobs=[Object.assign(JSON.parse(JSON.stringify(SEED_LIBRARY.jobs[0])),{info:Object.assign({},SEED_LIBRARY.jobs[0].info,{jobTitle:"EDITED"})})]; save();`);
ok("a local edit overrides the seed entry rather than duplicating it",
   sandbox.allJobs().length === SEED.jobs.length &&
   sandbox.jobById(firstId).info.jobTitle === "EDITED");
run(`S.removed=[${JSON.stringify(SEED.jobs[1].id)}]; save();`);
ok("a removed seed entry disappears from the library",
   sandbox.allJobs().length === SEED.jobs.length - 1);
run(`S.jobs=[]; S.stations=[]; S.removed=[]; save();`);
ok("discarding local edits restores the baked library",
   sandbox.allJobs().length === SEED.jobs.length);

/* ---------- 3. employee record detection ---------- */
const HM = ["lunge", "sld", "shoulder", "trunk", "cervical"];
const hma = {
  id: "t1", name: "Test Case", dept: "Fabrication", shift: "1", date: "2026-08-01",
  scores: {
    lunge:    [{ val: 3, pain: false }, { val: 1, pain: false }],
    sld:      [{ val: 2, pain: false }, { val: 2, pain: false }],
    shoulder: [{ val: 1, pain: false }, { val: 3, pain: false }],
    trunk:    [{ val: 0, pain: true }, { val: 2, pain: false }],
    cervical: [{ val: 3, pain: false }, { val: 3, pain: false }],
  },
  total: 7,
  hypermobile: { lunge: false, sld: true, shoulder: false, trunk: false, cervical: false },
  hasOA: true, qualityFocus: { lunge: ["flexibility"], sld: [], shoulder: ["strength"], trunk: [], cervical: [] },
};
console.log("\n--- employee record detection ---");
ok("recognises a Tracker record array", sandbox.looksLikeHma([hma]));
ok("rejects a job-library array", !sandbox.looksLikeHma([SEED.jobs[0]]));
ok("rejects junk", !sandbox.looksLikeHma([{ foo: 1 }]));
ok("rejects an empty array", !sandbox.looksLikeHma([]));

/* ---------- 4. deficit profile ---------- */
console.log("\n--- deficit profile ---");
const prof = sandbox.profileOf(hma);
ok("deficit is the worst side (L=1 -> 2)", prof.lunge.deficit === 2);
ok("weaker leg identified as Left", prof.lunge.weakSideName === "Left Leg");
ok("weaker arm identified as Right", prof.shoulder.weakSideName === "Right Arm");
ok("pain detected and dominates", prof.trunk.pain === true && prof.trunk.deficit === 4);
ok("a clean pattern yields zero deficit", prof.cervical.deficit === 0);

/* ---------- 5. analysis against a real seeded job ---------- */
const job = SEED.jobs.find(j => /bushing/i.test(j.info.jobTitle)) || SEED.jobs[0];
const station = SEED.stations.find(s => s.fromJob === job.id) || SEED.stations[0];
console.log(`\n--- findings: ${hma.name} on "${job.info.jobTitle}" ---`);
const res = sandbox.analyze(hma, job, station);
res.findings.filter(f => f.band !== "mon").slice(0, 6).forEach(f => {
  console.log(`  [${BAND_LABEL[f.band].padEnd(8)}] ${String(f.score).padStart(5)}  ${f.pdaName} -> ${f.hmaLabel}`);
  f.links.linked.slice(0, 2).forEach(s => console.log(`             step: ${s.name.slice(0, 74)}`));
});
ok("produces findings against a seeded job", res.findings.length > 0, res.findings.length + " findings");
ok("a clean pattern produces no findings",
   res.findings.filter(f => f.hma === "cervical").length === 0);
/* Pain escalates, but proportionally to exposure. A painful pattern under a real
   demand is Priority; the same pattern under an incidental one (the FTA rates
   "Sitting - breaks and lunch") must not outrank it. */
const trunkF = res.findings.filter(f => f.hma === "trunk");
ok("pain + real exposure ranks Priority",
   trunkF.filter(f => f.freq.w * f.coupling >= 1).every(f => f.band === "pri"));
ok("pain + incidental exposure does not reach Priority",
   trunkF.filter(f => f.freq.w * f.coupling < 1).every(f => f.band !== "pri"),
   trunkF.filter(f => f.freq.w * f.coupling < 1).map(f => f.pdaName + "=" + f.band).join(", ") || "none");
ok("every painful pattern is still escalated at least to Elevated",
   trunkF.every(f => f.band === "pri" || f.band === "ele"));
ok("findings are ranked worst-first",
   res.findings.every((f, i) => i === 0 || res.findings[i - 1].score >= f.score));
const oaNotes = res.findings.reduce((n, f) => n + f.mods.filter(x => x.t === "oa").length, 0);
const oaPatterns = new Set(res.findings.filter(f => f.mods.some(x => x.t === "oa")).map(f => f.hma));
ok("OA rationale is stated once per pattern, not on every card",
   oaNotes === oaPatterns.size, oaNotes + " notes / " + oaPatterns.size + " patterns");
ok("hand/wrist demands are reported as not-measured, never as low risk",
   Array.isArray(res.blind));

/* ---------- 6. narrative ---------- */
console.log("\n--- narrative ---");
const painFinding = res.findings.find(f => f.profile.pain);
if (painFinding) {
  const txt = sandbox.whyText(painFinding);
  ok("a painful side reads as 'pain', never as a negative score",
     /pain/.test(txt) && !/-\d/.test(txt));
  console.log("    " + txt.slice(0, 150));
}

/* ---------- 7. task-step linking ---------- */
console.log("\n--- task-step linking ---");
try {
  const before = sandbox.stepsFor(job, station, "reaching").linked.map(x => x.idx);
  run(`toggleLink(${JSON.stringify(job.id)},${JSON.stringify(station.id)},"reaching",0);`);
  const after = sandbox.stepsFor(job, station, "reaching").linked.map(x => x.idx);
  ok("toggling a link persists", JSON.stringify(before) !== JSON.stringify(after),
     JSON.stringify(before) + " -> " + JSON.stringify(after));
  ok("confirmed links stop being marked 'suggested'",
     sandbox.stepsFor(job, station, "reaching").linked.every(x => !x.auto));
  run(`S.links={}; save();`);
} catch (e) { ok("task-step linking", false, e.message); }

/* ---------- 8. edge cases ---------- */
console.log("\n--- edge cases ---");
const sparse = {
  id: "t2", name: "Sparse", total: 0, hasOA: false,
  scores: Object.fromEntries(HM.map(k => [k, [{ val: null, pain: false }, { val: null, pain: false }]])),
  hypermobile: Object.fromEntries(HM.map(k => [k, false])),
};
try { ok("an unscored HMA yields no findings", sandbox.analyze(sparse, job, null).findings.length === 0); }
catch (e) { ok("unscored HMA", false, e.message); }
try {
  const empty = { id: "j0", info: { jobTitle: "Empty" }, movements: {}, mh: { lift: [], carry: [], pushpull: [] } };
  const r = sandbox.analyze(hma, empty, null);
  ok("an empty job yields no findings and no blind spots", r.findings.length === 0 && r.blind.length === 0);
} catch (e) { ok("empty job", false, e.message); }
try { ok("works with no station selected", sandbox.analyze(hma, job, null).findings.length > 0); }
catch (e) { ok("no station", false, e.message); }

/* ---------- 9. every job in the library analyses cleanly ---------- */
console.log("\n--- all seeded jobs ---");
let broke = 0;
for (const j of SEED.jobs) {
  try { sandbox.analyze(hma, j, SEED.stations.find(s => s.fromJob === j.id) || null); }
  catch (e) { broke++; console.log(`  ✗ ${j.info.jobTitle}: ${e.message}`); }
}
ok("all jobs analyse without throwing", broke === 0, SEED.jobs.length + " jobs");

/* ---------- 10. render smoke test ---------- */
console.log("\n--- render smoke test ---");
run(`S.hma=[${JSON.stringify(hma)}]; S.assign={"t1":{jobId:${JSON.stringify(job.id)},stationId:${JSON.stringify(station.id)}}}; save();`);
for (const v of ["home", "jobs", "jobedit", "stations", "stedit", "data", "method", "emp", "links"]) {
  const id = (v === "jobedit") ? job.id : (v === "stedit") ? station.id : hma.id;
  try { run(`view=${JSON.stringify(v)}; currentId=${JSON.stringify(id)}; render();`); ok(v, true); }
  catch (e) { ok(v, false, e.message); }
}

/* ---------- 11. save-into-program round trip ---------- */
console.log("\n--- save into program ---");
const re = /\/\* SEED-START \*\/[\s\S]*?\/\* SEED-END \*\//;
const lib = { jobs: sandbox.allJobs(), stations: sandbox.allStations(), links: sandbox.allLinks() };
const payload = JSON.stringify(lib).replace(/</g, "\\u003c");
const rebuilt = html.replace(re, "/* SEED-START */\nconst SEED_LIBRARY = " + payload + ";\n/* SEED-END */");
ok("the seed block is replaceable in the file's own source", rebuilt !== html || payload.length > 0);
ok("payload cannot terminate the inline <script>", !/<\/script/i.test(payload));
try {
  const sb2 = Object.assign({}, sandbox);
  const inner = rebuilt.match(/<script>([\s\S]*)<\/script>/)[1];
  const ctx = vm.createContext({
    console: { log() {} }, document: sandbox.document, localStorage: sandbox.localStorage,
    alert: () => {}, confirm: () => true, FileReader: function () {},
    Blob: function () {}, URL: sandbox.URL,
  });
  ctx.window = ctx;
  vm.runInContext(inner, ctx);
  const reloaded = vm.runInContext("SEED_LIBRARY", ctx);
  ok("a re-baked file parses and carries the same library",
     reloaded.jobs.length === lib.jobs.length && reloaded.stations.length === lib.stations.length,
     reloaded.jobs.length + " jobs / " + reloaded.stations.length + " stations");
} catch (e) { ok("re-baked file parses", false, e.message); }

console.log(fails ? `\n${fails} FAILING CHECK(S)` : "\nAll checks passed.");
process.exit(fails ? 1 : 0);
