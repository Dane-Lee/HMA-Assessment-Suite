# -*- coding: utf-8 -*-
"""
Build the self-contained @font-face block for Barlow / Barlow Condensed.

The HMA Tracker gets these from Google Fonts via a <link>. This app is opened as a
local file and is documented as making no network calls, so a <link> would both
break that promise and silently fall back to Arial on a plant machine with no
internet (Barlow Condensed is not installed on Windows by default).

So the latin subsets are downloaded once, here, and embedded as base64 data: URIs.
After that the app needs no network and no installed fonts, on any machine.

Run only when the typeface set changes:
    python tools/embed-fonts.py     ->  tools/fonts.css
then paste/inject the result into the app's <style> block (inject-fonts.py).
"""
import re, io, os, base64, sys
import urllib.request

OUT = os.path.join("tools", "fonts.css")
API = ("https://fonts.googleapis.com/css2"
       "?family=Barlow:wght@400;600;700"
       "&family=Barlow+Condensed:wght@600;700;800"
       "&display=swap")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else data.decode("utf8")


def main():
    css = get(API)

    # Google emits one @font-face per (family, weight, subset), each preceded by a
    # /* subset */ comment. Keep latin only - these documents are English.
    blocks = re.split(r'/\*\s*([a-z\-]+)\s*\*/', css)
    faces = []
    for i in range(1, len(blocks) - 1, 2):
        subset, body = blocks[i], blocks[i + 1]
        if subset != "latin":
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", body)
        wt = re.search(r"font-weight:\s*(\d+)", body)
        url = re.search(r"src:\s*url\(([^)]+)\)", body)
        if fam and wt and url:
            faces.append((fam.group(1), wt.group(1), url.group(1)))

    if not faces:
        print("No latin faces parsed - Google may have changed the response format.")
        sys.exit(1)

    out = ["/* Barlow + Barlow Condensed, latin subset, embedded so the app needs no",
           "   network and no installed fonts. Regenerate with tools/embed-fonts.py. */"]
    total = 0
    for fam, wt, url in faces:
        raw = get(url, binary=True)
        total += len(raw)
        b64 = base64.b64encode(raw).decode("ascii")
        out.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}" % (fam, wt, b64))
        print("  %-18s %-4s %6.1f KB" % (fam, wt, len(raw) / 1024.0))

    with io.open(OUT, "w", encoding="utf8") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n%d faces, %.1f KB raw -> %.1f KB base64 -> %s"
          % (len(faces), total / 1024.0, os.path.getsize(OUT) / 1024.0, OUT))


main()
