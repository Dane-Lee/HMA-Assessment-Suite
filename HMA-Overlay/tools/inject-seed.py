# -*- coding: utf-8 -*-
"""
Bake tools/seed-library.json into the app HTML, between the SEED-START/SEED-END markers.

This is the same operation the app's "Save into program" button performs in the
browser; this script is the build-time path used after re-running the FTA parser.

  python tools/parse-ftas.py      # FTAs  -> seed-library.json
  python tools/make-stations.py   # adds derived stations
  python tools/inject-seed.py     # bakes it into "HMA Overlay.html"
"""
import json, io, re, os, sys

SEED = os.path.join("tools", "seed-library.json")
HTML = "HMA Overlay.html"

START = "/* SEED-START */"
END = "/* SEED-END */"


def main():
    if not os.path.exists(SEED):
        print("Missing", SEED, "- run tools/parse-ftas.py first")
        sys.exit(1)
    lib = json.load(io.open(SEED, encoding="utf8"))
    lib.setdefault("links", {})
    payload = json.dumps(lib, ensure_ascii=False, separators=(",", ":"))
    # never let the payload terminate the inline <script>
    payload = payload.replace("<", "\\u003c")

    html = io.open(HTML, encoding="utf8").read()
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pat.search(html):
        print("Markers not found in", HTML)
        sys.exit(1)

    block = START + "\nconst SEED_LIBRARY = " + payload + ";\n" + END
    html = pat.sub(lambda _: block, html, count=1)
    io.open(HTML, "w", encoding="utf8").write(html)

    print("Baked %d jobs, %d stations into %s"
          % (len(lib.get("jobs", [])), len(lib.get("stations", [])), HTML))
    print("Payload size: %.1f KB" % (len(payload) / 1024.0))


main()
