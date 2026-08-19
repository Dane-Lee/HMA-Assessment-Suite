# -*- coding: utf-8 -*-
"""
Scaffold a station (JSA-shaped) task list for each seeded FTA job.

The FTA's per-movement "task" column is, in effect, the job's task-step list -
"Applying lube to bushings, placing beams into bushings press" and so on. That is
close enough to a JSA task row to seed the step-linking side of the app, and far
better than making the user type all of it.

These are explicitly marked  derived: true  and labelled "from FTA" in the UI.
They are NOT real JSAs: no hazard assessment was performed, so hazard types are
left empty for the user to fill in. A real JSA export always supersedes one of
these (matched on station name).

Word mangles these cells when the source had a line break, producing runs like
"Lever and Bush Press buttonsPlacing beams into bush press". Splitting on a
lowercase->uppercase boundary recovers the original two steps.

Reads/writes tools/seed-library.json in place.
"""
import json, io, re, os

SEED = os.path.join("tools", "seed-library.json")

# steps that describe a body position rather than a job task - not useful as JSA rows
NOISE = re.compile(
    r'^(for |with or without|r ?/ ?l|single or both|critical for safety|full / partial|'
    r'partial / sustained|as needed|n/?a|not a required function)', re.I)

BOILERPLATE = re.compile(
    r'^(standing|walking|sitting|squatting|kneeling|reaching|bending|climbing|balancing|'
    r'most tasks|all work tasks|all tasks|various tasks)[\s.]*$', re.I)


def split_steps(text):
    """Recover discrete task steps from one FTA task cell."""
    if not text:
        return []
    # Word dropped the line break: "buttonsPlacing" -> "buttons. Placing"
    t = re.sub(r'([a-z,)])([A-Z])', r'\1. \2', text)
    parts = re.split(r'(?:\.\s+|;\s*|\s*\|\s*)', t)
    out = []
    for p in parts:
        p = p.strip(" .;,-")
        if len(p) < 6 or len(p) > 110:
            continue
        if NOISE.match(p) or BOILERPLATE.match(p):
            continue
        p = p[0].upper() + p[1:]
        out.append(p)
    return out


def main():
    data = json.load(io.open(SEED, encoding="utf8"))
    stations = []
    for job in data["jobs"]:
        seen, steps = set(), []
        for mid, m in job["movements"].items():
            if not m.get("task") or m.get("freq") in ("", "never"):
                continue
            for s in split_steps(m["task"]):
                k = re.sub(r'[^a-z0-9]', '', s.lower())
                if k and k not in seen:
                    seen.add(k)
                    steps.append(s)
        title = job["info"]["jobTitle"]
        stations.append({
            "id": "seedjsa-" + re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'),
            "seed": True, "derived": True,
            "head": {"workstation": title, "department": "", "site": "Somerset, KY",
                     "obsDates": "", "lead": "", "team": "", "reviewedBy": "", "ppe": ""},
            "tasks": [{"name": s, "hazards": [], "reduction": "", "actions": []}
                      for s in steps[:14]],
            "fromJob": job["id"],
        })
    data["stations"] = stations
    with io.open(SEED, "w", encoding="utf8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)

    print("%-28s %s" % ("STATION (derived from FTA)", "steps"))
    print("-" * 40)
    for s in stations:
        print("%-28s %5d" % (s["head"]["workstation"][:28], len(s["tasks"])))
    print("\n%d stations -> %s" % (len(stations), SEED))
    print("\nSample - %s:" % stations[-1]["head"]["workstation"])
    for t in stations[-1]["tasks"][:8]:
        print("   -", t["name"][:88])


main()
