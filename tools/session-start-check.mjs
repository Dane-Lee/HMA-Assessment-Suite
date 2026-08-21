#!/usr/bin/env node
/* SessionStart hook: fetch, report staleness, surface the newest handoff entry.

   Two Claude sessions work this estate from two machines and cannot see each
   other. Staleness is invisible without fetching — on 2026-08-20 a session was 7
   commits behind and nearly ran `git subtree split` from dead history. CLAUDE.md
   asked sessions to fetch first, but a document is advisory. This runs whether or
   not anyone remembers.

   Emits JSON on stdout: additionalContext reaches the model, systemMessage the user.
*/

import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const REPOS = [['suite', '.'], ['Tracker', 'HMA-Tracker-app'], ['Cadence', 'HMA-Cadence']];

const sh = (cmd, cwd) => {
  try { return execSync(cmd, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); }
  catch { return null; }
};

const lines = [];
const alerts = [];

for (const [label, dir] of REPOS) {
  const cwd = path.join(root, dir);
  if (!fs.existsSync(path.join(cwd, '.git'))) { lines.push(`${label}: not cloned here`); continue; }
  sh('git fetch --quiet', cwd);
  const counts = sh('git rev-list --left-right --count @{u}...HEAD', cwd);
  const dirty = (sh('git status --porcelain', cwd) || '').split('\n').filter(Boolean).length;
  if (!counts) { lines.push(`${label}: no upstream tracking branch`); continue; }
  const [behind, ahead] = counts.split(/\s+/).map(Number);
  const bits = [];
  if (behind) { bits.push(`${behind} BEHIND`); alerts.push(`${label} is ${behind} commit(s) behind origin`); }
  if (ahead) bits.push(`${ahead} ahead`);
  if (dirty) bits.push(`${dirty} uncommitted`);
  lines.push(`${label}: ${bits.length ? bits.join(', ') : 'in sync'}`);
}

/* Newest handoff entry — the other session's most recent word. */
let handoff = 'HANDOFF.md not found';
const hp = path.join(root, 'HANDOFF.md');
if (fs.existsSync(hp)) {
  const all = fs.readFileSync(hp, 'utf8').split('\n');
  const i = all.findIndex((l) => l.startsWith('## '));
  if (i !== -1) {
    const heading = all[i].replace(/^##\s*/, '');
    const sub = all.slice(i + 1).find((l) => l.startsWith('### '));
    handoff = heading + (sub ? ` — ${sub.replace(/^###\s*/, '')}` : '');
  }
}

const body = [
  'HMA estate — session start check',
  ...lines.map((l) => `  ${l}`),
  `  newest handoff entry: ${handoff}`,
  alerts.length
    ? `  ACTION: ${alerts.join('; ')}. Pull before touching anything — the other machine has moved.`
    : '  Nothing is behind origin (uncommitted work, if listed above, is a separate matter).',
  '  Protocol (CLAUDE.md): read HANDOFF.md before starting; append an entry before finishing.',
].join('\n');

process.stdout.write(JSON.stringify({
  systemMessage: alerts.length ? `HMA: ${alerts.join('; ')} — pull before working.` : undefined,
  hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: body },
}));
