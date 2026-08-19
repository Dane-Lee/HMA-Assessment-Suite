# -*- coding: utf-8 -*-
"""
Parse the ATI FTA .docx files into the job-library seed baked into the app.

Reads  : Ergo Assessment Helper/source-data/FTA-examples-Somerset-editable/*.docx
Writes : tools/seed-library.json  (inject-seed.py bakes it into the HTML)

These documents describe JOBS, not people - no PHI is read or written.

Two places in each FTA carry frequency:
  * the summary grid  - a labeled 5-column chart, all 17 movements, always present
  * the detail rows   - richer (task text + notes) but sometimes missing a movement
Frequency is taken from the SUMMARY GRID (authoritative, and what the ATI FTA audit
checks), task text and notes from the detail rows. Disagreements between the two are
reported rather than silently resolved - the audit treats that as a document defect.

Movement labels are matched on letters only, because the source template contains
"CERVICAL SPINEMOTION" (missing space) in the detail rows of 8 of the 11 FTAs.

These are 2020-era FTAs on the older 5-level scale (Never/Minimal/Occasional/
Frequent/Constant). The current 2024 scale drops Minimal, so Minimal -> Occasional
(the lowest non-zero band). Nothing else is reinterpreted.
"""
import zipfile, re, glob, os, json, io, sys

SRC = os.path.join("..", "..", "Ergo Assessment Helper", "source-data",
                   "FTA-examples-Somerset-editable")
OUT = os.path.join("tools", "seed-library.json")

TXT  = re.compile(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', re.S)
ROW  = re.compile(r'<w:tr[ >].*?</w:tr>', re.S)
CELL = re.compile(r'<w:tc[ >].*?</w:tc>', re.S)


def key(s):
    return re.sub(r'[^A-Z]', '', (s or "").upper())


MOVE_ID = {key(k): v for k, v in {
    "SITTING": "sitting", "STANDING": "standing", "WALKING": "walking",
    "FORWARD BENDING": "forwardbending", "SQUATTING": "squatting", "KNEELING": "kneeling",
    "CRAWLING": "crawling", "CLIMBING": "climbing", "REACHING": "reaching",
    "BALANCING": "balancing", "CERVICAL SPINE MOTION": "cervical", "DRIVING": "driving",
    "LOWER EXTREMITIES": "lowerext", "SIMPLE GRASP": "simplegrasp",
    "FIRM GRASP": "firmgrasp", "FINE MANIPULATION": "finemanip", "PINCHING": "pinching",
}.items()}

ALL_IDS = ["sitting", "standing", "walking", "forwardbending", "squatting", "kneeling",
           "crawling", "climbing", "reaching", "balancing", "cervical", "driving",
           "lowerext", "simplegrasp", "firmgrasp", "finemanip", "pinching"]

GRID_COL = [("NEVER", "never"), ("MINIMAL", "occ"), ("OCCASIONAL", "occ"),
            ("FREQUENT", "freq"), ("CONSTANT", "const")]

FREQ_MAP = [(r'^NOTA?REQUI?REDFUNC', "never"), (r'^NA$', "never"),
            (r'^CONSTANT', "const"), (r'^FREQUENT', "freq"), (r'^OCCASIONAL', "occ"),
            (r'^MINIMAL', "occ"), (r'^RARELY', "occ")]

DEMAND_ORDER = ["", "never", "occ", "freq", "const"]

MH_FREQ = [("CONSTANT", "Constant"), ("FREQUENT", "Frequent"), ("OCCASIONAL", "Occasional"),
           ("MINIMAL", "Occasional"), ("RARELY", "Occasional")]

SMART = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "″": '"', "′": "'",
    "�": '"',
}


def clean(s):
    for a, b in SMART.items():
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s).strip()


def cells(tr):
    return [clean(''.join(TXT.findall(c))) for c in CELL.findall(tr)]


def map_freq(raw):
    k = key(raw)
    for pat, val in FREQ_MAP:
        if re.match(pat, k):
            return val
    return None


def mh_freq(raw):
    k = key(raw)
    for pat, val in MH_FREQ:
        if k.startswith(pat):
            return val
    return ""


def max_force(raw):
    """'Frequent7- 12 lbs.' -> 12 ; 'MinimalUp to 50lbsF' -> 50 ; 'Frequent<5 lbsF' -> 5"""
    body = re.sub(r'^(constant|frequent|occasional|minimal|rarely)', '', raw.strip(), flags=re.I)
    body = re.sub(r'\d+\s*-\s*\d+\s*(hours?|hrs?)', '', body, flags=re.I)
    body = re.sub(r'\(\s*[\d\-\s]+reps?/?hour\s*\)', '', body, flags=re.I)
    body = re.sub(r'\d+\s*%', '', body)
    nums = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', body)]
    return str(int(max(nums))) if nums else ""


def mh_row(ct):
    return {"item": ct[1], "freq": mh_freq(ct[2]), "force": max_force(ct[2]),
            "detail": ct[3] if len(ct) > 3 else ""}


def parse(path):
    xml = zipfile.ZipFile(path).read('word/document.xml').decode('utf8', 'replace')
    rows = [cells(tr) for tr in ROW.findall(xml)]

    grid, detail = {}, {}
    mh = {"lift": [], "carry": [], "pushpull": []}
    colmap, cur_mh, conflicts, unmapped = None, None, [], []

    for ct in rows:
        if not ct:
            continue

        # summary-grid header: learn column -> frequency from the printed labels
        if key(ct[0]) == "MOVEMENT" and any("NEVER" in key(c) for c in ct[1:]):
            colmap = {}
            for i, c in enumerate(ct[1:], start=1):
                for label, val in GRID_COL:
                    if label in key(c):
                        colmap[i] = val
                        break
            continue

        head = key(ct[0])

        # summary-grid body: an X marks the frequency column
        if colmap and head in MOVE_ID and len(ct) > 2 and any(c.upper() == "X" for c in ct[1:]):
            for i, c in enumerate(ct[1:], start=1):
                if c.upper() == "X" and i in colmap:
                    grid[MOVE_ID[head]] = colmap[i]
                    break
            continue

        # material handling
        if head in ("LIFT", "CARRY", "PUSHPULL"):
            cur_mh = {"LIFT": "lift", "CARRY": "carry"}.get(head, "pushpull")
            if len(ct) >= 3 and ct[1] and ct[2] and mh_freq(ct[2]):
                mh[cur_mh].append(mh_row(ct))
            continue
        if not ct[0] and cur_mh and len(ct) >= 3 and ct[1] and ct[2] and mh_freq(ct[2]):
            mh[cur_mh].append(mh_row(ct))
            continue

        # movement detail rows: task text + notes
        if head in MOVE_ID:
            mid = MOVE_ID[head]
            raw = ct[2] if len(ct) >= 3 and ct[2] else (ct[1] if len(ct) == 2 else "")
            task = ct[1] if len(ct) >= 3 else ""
            notes = ct[3] if len(ct) > 3 else ""
            fq = map_freq(raw) if raw else None
            if fq or task:
                prev = detail.get(mid)
                if not prev or len(task) > len(prev["task"]):
                    detail[mid] = {"freq": fq, "task": task, "notes": notes}
            elif raw and raw.upper() != "X":
                unmapped.append(raw[:60])
            cur_mh = None

    movements = {}
    for mid in ALL_IDS:
        d = detail.get(mid, {"freq": None, "task": "", "notes": ""})
        g = grid.get(mid)
        freq = g or d["freq"] or ""
        if g and d["freq"] and g != d["freq"]:
            # The source document contradicts itself. Resolve to the HIGHER demand:
            # under-reporting is the wrong failure direction for a risk tool. Press
            # Operator is the live example - its grid says squatting Never while the
            # detail row documents "placing axle on the lowest rack, partial/sustained".
            freq = max(g, d["freq"], key=lambda f: DEMAND_ORDER.index(f))
            conflicts.append("%s: grid=%s detail=%s -> kept %s" % (mid, g, d["freq"], freq))
        movements[mid] = {"freq": freq, "task": d["task"], "notes": d["notes"]}
    return movements, mh, conflicts, unmapped, len(grid)


def title_from(fn):
    t = os.path.basename(fn).replace(".docx", "")
    t = t.replace("Hendrickson-", "").replace("Hendrickson", "")
    t = re.sub(r'^FTA\s*', '', t)
    t = re.sub(r'-?\s*Somerset\s*KY\s*-?', '', t)
    return re.sub(r'^[\s-]+|[\s-]+$', '', t).strip()


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.docx")))
    if not files:
        print("No FTA .docx found at", SRC)
        sys.exit(1)

    jobs, rep, allc, allu = [], [], [], []
    for f in files:
        mv, mh, conf, un, ngrid = parse(f)
        title = title_from(f)
        jobs.append({
            "id": "seed-" + re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'),
            "seed": True,
            "info": {"client": "Hendrickson", "site": "Somerset, KY", "jobTitle": title,
                     "stationScope": "", "date": "", "consultant": ""},
            "movements": mv, "mh": mh, "source": os.path.basename(f),
            "conflicts": conf,
        })
        rep.append((title,
                    sum(1 for m in mv.values() if m["freq"]),
                    sum(1 for m in mv.values() if m["task"]),
                    sum(len(v) for v in mh.values()), ngrid))
        allc += ["%s -> %s" % (title, c) for c in conf]
        allu += un

    with io.open(OUT, "w", encoding="utf8") as fh:
        json.dump({"jobs": jobs}, fh, indent=1, ensure_ascii=False)

    print("%-26s %6s %5s %5s %5s" % ("JOB", "rated", "task", "MH", "grid"))
    print("-" * 52)
    for t, r, w, m, g in rep:
        print("%-26s %6d %5d %5d %5d" % (t[:26], r, w, m, g))
    print("\n%d jobs -> %s" % (len(jobs), OUT))
    print("\nUnmapped frequency strings:", sorted(set(allu)) or "none")
    print("Grid/detail frequency disagreements:", len(allc))
    for c in allc[:15]:
        print("   ", c)


main()
