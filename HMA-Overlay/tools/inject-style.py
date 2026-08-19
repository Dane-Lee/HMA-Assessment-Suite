# -*- coding: utf-8 -*-
"""
Bake tools/app.css (with tools/fonts.css inlined at its FONTS marker) into the
app's <style> block.

    python tools/embed-fonts.py    # once, or when the typeface set changes
    python tools/inject-style.py   # after any edit to tools/app.css
"""
import io, re, os, sys

CSS = os.path.join("tools", "app.css")
FONTS = os.path.join("tools", "fonts.css")
HTML = "HMA Overlay.html"


def main():
    if not os.path.exists(CSS):
        print("Missing", CSS); sys.exit(1)
    css = io.open(CSS, encoding="utf8").read()

    if os.path.exists(FONTS):
        fonts = io.open(FONTS, encoding="utf8").read()
        css = re.sub(r'/\* FONTS-START \*/[\s\S]*?/\* FONTS-END \*/',
                     lambda _: "/* FONTS-START */\n" + fonts + "/* FONTS-END */", css, count=1)
    else:
        print("WARNING:", FONTS, "not found - the app will fall back to Arial.")

    if "</style" in css:
        print("app.css contains a </style> sequence; refusing to inject."); sys.exit(1)

    html = io.open(HTML, encoding="utf8").read()
    new, n = re.subn(r'<style>[\s\S]*?</style>', lambda _: "<style>\n" + css + "\n</style>", html, count=1)
    if not n:
        print("No <style> block found in", HTML); sys.exit(1)
    io.open(HTML, "w", encoding="utf8").write(new)
    print("Injected %.1f KB of CSS into %s  (file now %.1f KB)"
          % (len(css) / 1024.0, HTML, os.path.getsize(HTML) / 1024.0))


main()
