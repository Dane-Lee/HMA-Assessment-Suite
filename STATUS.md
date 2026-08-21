# Estate status

_Generated 2026-08-21 12:34 UTC on `OHS-ET-kef9Mar3` by `node tools/estate-status.mjs`._

**Do not edit by hand — regenerate.** Every line below is the output of a command that
actually ran on the machine named above. A check that could not run says so.

## Repositories

| repo | remote | branch | ahead | behind | dirty | HEAD |
|---|---|---|---|---|---|---|
| HMA-Assessment-Suite | Dane-Lee/HMA-Assessment-Suite | main | 0 | 0 | 4 | 25bd0bf docs(handoff): record the s8 retirement, new t9, and the WebP conversion |
| HMA-Tracker-app | Dane-Lee/HMA-Correct-Exercise-Tracker | main | 0 | 0 | 2 | 6307736 Convert exercise images to WebP, wire 18 new ones, add exercise t9 |
| HMA-Cadence | Dane-Lee/HMA-Cadence | main | 0 | 0 | 0 | 1cb7a8a docs: add Copilot Studio capability probe for the Cadence backend |

`ahead`/`behind` are versus `origin`. Anything non-zero means this machine and the
remote disagree — resolve that before trusting anything else on this page.

## Checks

| app | command | available | result |
|---|---|---|---|
| HMA-Tracker-app | `npm test` | defined | 9 pass, 0 fail |
| HMA-Cadence | `npm test` | defined, deps NOT installed here | not run |
| api + HMA-Manual | `pytest` | .venv present | 86 passed, 1 skipped |
| HMA-Tracker-app | `npm run build` | defined | builds |

## Exercise artwork

**54 of 60 exercises have an image.**

Still needed:

- l2 Pigeon Stretch
- s5 Single Leg Stance
- t1 Child Pose with Cross Reach
- c3 Sternocleidomastoid Stretch
- c9 Thread the Needle with Extension
- co5 Anti Rotation Squat

