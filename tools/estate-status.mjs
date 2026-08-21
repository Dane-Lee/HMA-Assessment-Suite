#!/usr/bin/env node
/* Generate STATUS.md — the estate's state as *derived facts*, never as claims.

   This exists because the handoff log recorded "Tracker npm install was run; npm
   test passes" when the Tracker had no test script at all. Nobody could check it,
   and it cost a session's worth of confusion. Anything in STATUS.md came out of a
   command that actually ran on the machine that generated it. If a check could not
   run, that is reported too — "not installed" is a fact; silence is not.

   Run from the repo root:  node tools/estate-status.mjs
*/

import { execSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const sh = (cmd, cwd = root) => {
  try {
    return { ok: true, out: execSync(cmd, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim() };
  } catch (e) {
    return { ok: false, out: `${e.stdout || ''}${e.stderr || ''}`.trim() || String(e.message) };
  }
};

const REPOS = [
  { name: 'HMA-Assessment-Suite', dir: '.' },
  { name: 'HMA-Tracker-app', dir: 'HMA-Tracker-app' },
  { name: 'HMA-Cadence', dir: 'HMA-Cadence' },
];

function repoRow({ name, dir }) {
  const cwd = path.join(root, dir);
  if (!fs.existsSync(path.join(cwd, '.git'))) return { name, missing: true };
  sh('git fetch --quiet', cwd);
  const remote = sh('git remote get-url origin', cwd).out.replace(/^https:\/\/github\.com\//, '').replace(/\.git$/, '');
  const branch = sh('git rev-parse --abbrev-ref HEAD', cwd).out;
  const head = sh('git log -1 --format="%h %s"', cwd).out;
  const counts = sh('git rev-list --left-right --count @{u}...HEAD', cwd);
  const [behind, ahead] = counts.ok ? counts.out.split(/\s+/) : ['?', '?'];
  const dirty = sh('git status --porcelain', cwd).out.split('\n').filter(Boolean).length;
  return { name, remote, branch, head, ahead, behind, dirty };
}

/* Which check commands genuinely exist, and what they return when run here.

   Each row names the ref it ran against. A check result without a ref is what
   caused the 2026-08-20/21 npm-test disagreement: the same command was truthfully
   "passing" on one branch and absent on another, and the claim recorded neither. */
function refOf(dir) {
  const cwd = path.join(root, dir);
  const b = sh('git rev-parse --abbrev-ref HEAD', cwd).out;
  const h = sh('git rev-parse --short HEAD', cwd).out;
  return b && h ? `${b}@${h}` : 'unknown ref';
}

function checks() {
  const rows = [];

  for (const app of ['HMA-Tracker-app', 'HMA-Cadence']) {
    const ref = refOf(app);
    const pkg = path.join(root, app, 'package.json');
    if (!fs.existsSync(pkg)) { rows.push([app, 'npm test', 'no package.json', '—', ref]); continue; }
    const scripts = JSON.parse(fs.readFileSync(pkg, 'utf8')).scripts || {};
    if (!scripts.test) { rows.push([app, 'npm test', 'NO test script defined', '—', ref]); continue; }
    if (!fs.existsSync(path.join(root, app, 'node_modules'))) {
      rows.push([app, 'npm test', 'defined, deps NOT installed here', 'not run', ref]);
      continue;
    }
    const r = sh('npm test --silent', path.join(root, app));
    const m = r.out.match(/# pass (\d+)[\s\S]*?# fail (\d+)/);
    rows.push([app, 'npm test', 'defined', m ? `${m[1]} pass, ${m[2]} fail` : (r.ok ? 'passed' : 'FAILED'), ref]);
  }

  const venv = path.join(root, '.venv', 'Scripts', 'python.exe');
  const py = fs.existsSync(venv) ? venv : (fs.existsSync(path.join(root, '.venv/bin/python')) ? path.join(root, '.venv/bin/python') : null);
  if (!py) {
    rows.push(['api + HMA-Manual', 'pytest', 'no .venv here', 'not run', refOf('.')]);
  } else {
    const r = sh(`"${py}" -m pytest -q`);
    const m = r.out.match(/(\d+) passed(?:, (\d+) skipped)?|(\d+) failed/);
    rows.push(['api + HMA-Manual', 'pytest', '.venv present', m ? m[0] : (r.ok ? 'passed' : 'FAILED'), refOf('.')]);
  }

  for (const app of ['HMA-Tracker-app']) {
    const r = sh('npm run build --silent', path.join(root, app));
    rows.push([app, 'npm run build', 'defined', r.ok ? 'builds' : 'FAILED', refOf(app)]);
  }
  return rows;
}

/* Artwork progress, read out of the Tracker's own test output rather than restated. */
function artwork() {
  const app = path.join(root, 'HMA-Tracker-app');
  if (!fs.existsSync(path.join(app, 'node_modules'))) return null;
  const r = sh('npm test --silent', app);
  const have = r.out.match(/(\d+)\/(\d+) exercises have an image/);
  const need = [...r.out.matchAll(/still needed: (\S+)\s+(.+)/g)].map((m) => `${m[1]} ${m[2].trim()}`);
  return have ? { have: have[1], total: have[2], need } : null;
}

const rows = REPOS.map(repoRow);
const chk = checks();
const art = artwork();

const L = [];
L.push('# Estate status');
L.push('');
L.push(`_Generated ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC on \`${os.hostname()}\` by \`node tools/estate-status.mjs\`._`);
L.push('');
L.push('**Do not edit by hand — regenerate.** Every line below is the output of a command that');
L.push('actually ran on the machine named above. A check that could not run says so.');
L.push('');
L.push('## Repositories');
L.push('');
L.push('| repo | remote | branch | ahead | behind | dirty | HEAD |');
L.push('|---|---|---|---|---|---|---|');
for (const r of rows) {
  if (r.missing) { L.push(`| ${r.name} | **not cloned on this machine** | — | — | — | — | — |`); continue; }
  L.push(`| ${r.name} | ${r.remote} | ${r.branch} | ${r.ahead} | ${r.behind} | ${r.dirty} | ${r.head} |`);
}
L.push('');
L.push('`ahead`/`behind` are versus `origin`. Anything non-zero means this machine and the');
L.push('remote disagree — resolve that before trusting anything else on this page.');
L.push('');
L.push('## Checks');
L.push('');
L.push('| app | command | available | result | ref |');
L.push('|---|---|---|---|---|');
for (const c of chk) L.push(`| ${c[0]} | \`${c[1]}\` | ${c[2]} | ${c[3]} | ${c[4] || '?'} |`);
L.push('');
L.push('The `ref` column is the point: the same command can be truthfully passing on one branch and');
L.push('absent on another. A result without a ref is not a fact, it is half of one.');
L.push('');
if (art) {
  L.push('## Exercise artwork');
  L.push('');
  L.push(`**${art.have} of ${art.total} exercises have an image.**`);
  if (art.need.length) {
    L.push('');
    L.push('Still needed:');
    L.push('');
    for (const n of art.need) L.push(`- ${n}`);
  }
  L.push('');
}
fs.writeFileSync(path.join(root, 'STATUS.md'), L.join('\n') + '\n');
console.log(L.join('\n'));
