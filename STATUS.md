# Estate status

_Generated 2026-08-21 15:13 UTC on `OHS-ET-kef9Mar3` by `node tools/estate-status.mjs`._

**Do not edit by hand — regenerate.** Every line below is the output of a command that
actually ran on the machine named above. A check that could not run says so.

## Repositories

| repo | remote | branch | ahead | behind | dirty | HEAD |
|---|---|---|---|---|---|---|
| HMA-Assessment-Suite | Dane-Lee/HMA-Assessment-Suite | main | 0 | 0 | 3 | e947c65 Record E12 (no payload slimming), the program key, and catch-up |
| HMA-Tracker-app | Dane-Lee/HMA-Correct-Exercise-Tracker | main | 0 | 0 | 0 | 2cbe19e Wire the last four exercise images |
| HMA-Cadence | Dane-Lee/HMA-Cadence | main | 0 | 0 | 0 | 1cb7a8a docs: add Copilot Studio capability probe for the Cadence backend |

`ahead`/`behind` are versus `origin`. Anything non-zero means this machine and the
remote disagree — resolve that before trusting anything else on this page.

## Checks

| app | command | available | result | ref |
|---|---|---|---|---|
| HMA-Tracker-app | `npm test` | defined | 9 pass, 0 fail | main@2cbe19e |
| HMA-Cadence | `npm test` | defined, deps NOT installed here | not run | main@1cb7a8a |
| api + HMA-Manual | `pytest` | .venv present | 86 passed, 1 skipped | main@e947c65 |
| HMA-Tracker-app | `npm run build` | defined | builds | main@2cbe19e |

The `ref` column is the point: the same command can be truthfully passing on one branch and
absent on another. A result without a ref is not a fact, it is half of one.

## Exercise artwork

**58 of 60 exercises have an image.**

Still needed:

- l2 Pigeon Stretch
- t1 Child Pose with Cross Reach

