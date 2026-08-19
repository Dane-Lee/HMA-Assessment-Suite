# -*- coding: utf-8 -*-
"""
One-time markup/JS migration to the Tracker's visual language.

Swaps the old floating nav for the Tracker's red header bar + black tab strip,
moves the dark-mode flag from <html class="light"> to <body class="dark"> (the
Tracker's convention, and light-default like the Tracker), and adapts the few
render functions whose emitted structure changed (findings gained a .fbody wrapper,
score tiles gained a .foot row and a hypermobility state).

Idempotent: re-running detects the new markup and does nothing.
"""
import io, sys

HTML = "HMA Overlay.html"
s = io.open(HTML, encoding="utf8").read()
orig = s
done = []


def swap(old, new, label, count=1):
    global s
    if new in s and old not in s:
        done.append("  = " + label + " (already applied)")
        return
    if s.count(old) != count:
        print("!! anchor not found (%d matches, expected %d): %s" % (s.count(old), count, label))
        sys.exit(1)
    s = s.replace(old, new, count)
    done.append("  + " + label)


# ---------------------------------------------------------------- header + tabs
old_header = '''<header class="top noprint">
  <div class="brand">HMA <span>Overlay</span><small>INDIVIDUAL JOB-DEMAND MATCH · ADMIN ONLY</small></div>
  <div class="spacer"></div>
  <button class="ghost sm" onclick="go('home')">Employees</button>
  <button class="ghost sm" onclick="go('jobs')">Jobs</button>
  <button class="ghost sm" onclick="go('stations')">Stations</button>
  <button class="ghost sm" onclick="go('data')">Data</button>
  <button class="ghost sm" onclick="go('method')">Method</button>
  <button class="ghost sm" onclick="toggleTheme()" id="themeBtn">Light</button>
</header>'''
new_header = '''<header class="header noprint">
  <div class="header-logo">ATI</div>
  <h1>HMA Overlay</h1>
  <div class="header-sub">Individual Job-Demand Match &middot; Admin Only</div>
  <button class="dark-toggle" id="themeBtn" onclick="toggleTheme()">Dark</button>
</header>
<nav class="tabs noprint">
  <button class="tab" data-view="home" onclick="go('home')">Employees</button>
  <button class="tab" data-view="jobs" onclick="go('jobs')">Jobs</button>
  <button class="tab" data-view="stations" onclick="go('stations')">Stations</button>
  <button class="tab" data-view="data" onclick="go('data')">Records</button>
  <button class="tab" data-view="method" onclick="go('method')">Method</button>
</nav>'''
swap(old_header, new_header, "Tracker header bar + tab strip")

# ---------------------------------------------------------------- active tab + theme label
old_render = '''function render(){
  const tb = document.getElementById("themeBtn");
  if (tb) tb.textContent = document.documentElement.classList.contains("light") ? "Dark" : "Light";'''
new_render = '''/* sub-screens light up the tab they belong to */
const TAB_OF = { home:"home", emp:"home", links:"home", jobs:"jobs", jobedit:"jobs",
                 stations:"stations", stedit:"stations", data:"data", method:"method" };
function render(){
  const dark = document.body && document.body.classList.contains("dark");
  const tb = document.getElementById("themeBtn");
  if (tb) tb.textContent = dark ? "Light" : "Dark";
  if (document.querySelectorAll){
    document.querySelectorAll(".tab").forEach(t =>
      t.classList.toggle("active", t.getAttribute("data-view") === TAB_OF[view]));
  }'''
swap(old_render, new_render, "active-tab highlighting")

# ---------------------------------------------------------------- theme: body.dark, light default
old_theme = '''function toggleTheme(){
  document.documentElement.classList.toggle("light");
  try { localStorage.setItem("hmaOverlay.theme", document.documentElement.classList.contains("light") ? "light" : "dark"); } catch(e){}
  render();
}
try { if (localStorage.getItem("hmaOverlay.theme") === "light") document.documentElement.classList.add("light"); } catch(e){}'''
new_theme = '''/* Same convention as the Tracker: light by default, body.dark opts in. */
function toggleTheme(){
  document.body.classList.toggle("dark");
  try { localStorage.setItem("hmaOverlay.theme", document.body.classList.contains("dark") ? "dark" : "light"); } catch(e){}
  render();
}
try { if (localStorage.getItem("hmaOverlay.theme") === "dark") document.body.classList.add("dark"); } catch(e){}'''
swap(old_theme, new_theme, "dark mode moved to body.dark (light default)")

# ---------------------------------------------------------------- save: strip body theme class
swap('''  const appEl = clone.querySelector("#app");
  if (appEl) appEl.innerHTML = "";          // don't bake the rendered screen
  clone.removeAttribute("class");           // don't bake the current theme''',
     '''  const appEl = clone.querySelector("#app");
  if (appEl) appEl.innerHTML = "";          // don't bake the rendered screen
  const bodyEl = clone.querySelector("body");
  if (bodyEl) bodyEl.removeAttribute("class");   // don't bake the current theme''',
     "save-into-program strips the theme class from body")

# ---------------------------------------------------------------- score tiles
swap('''    return `<div class="sb ${cls}">
      <div class="n">${esc(m.label)}</div><div class="v">${v}</div>
      <div class="small dim" style="margin-top:3px">R / L${tags.length?" ":""}${tags.join(" ")}</div></div>`;''',
     '''    return `<div class="sb ${cls}">
      <div class="n">${esc(m.label)}</div><div class="v">${v}</div>
      <div class="foot">R / L${tags.length?"<br>":""}${tags.join(" ")}</div></div>`;''',
     "score tile footer")

swap('''    const cls = P.pain ? "painful" : P.asym >= 1 ? "asym" : "";''',
     '''    const cls = P.pain ? "painful" : P.hyper ? "hyper" : P.asym >= 1 ? "asym" : "";''',
     "score tile hypermobility state")

swap('''    if (P.hyper) tags.push(`<span class="pill out">hyper</span>`);''',
     '''    if (P.hyper) tags.push(`<span class="pill hyper">hyper</span>`);''',
     "hypermobility pill uses the Tracker's blue")

swap('''      ${rec.hasOA?`<span><span class="pill out">OA</span> flagged on this record</span>`:""}''',
     '''      ${rec.hasOA?`<span><span class="pill oa">OA</span> flagged on this record</span>`:""}''',
     "OA pill uses the Tracker's orange")

swap('''        <div style="font-size:19px;font-weight:700">${rec.total}<span class="dim" style="font-size:14px">/15</span></div></div>''',
     '''        <div class="total-num" style="font-size:34px">${rec.total}<span class="dim" style="font-size:17px">/15</span></div></div>''',
     "HMA total uses the Tracker's numeral treatment")

# ---------------------------------------------------------------- findings: .fbody wrapper
swap('''    return `<div class="finding ${fd.band}">
      <div class="fhead">
        <div class="ftitle">${esc(fd.pdaName)} <span class="dim" style="font-weight:400">→ ${esc(fd.hmaLabel)}</span></div>
        <span class="pill ${fd.band}">${BAND_LABEL[fd.band]}</span>
      </div>
      ${steps.length''',
     '''    return `<div class="finding ${fd.band}">
      <div class="fhead">
        <div class="ftitle">${esc(fd.pdaName)} <span class="arrow">→</span> ${esc(fd.hmaLabel)}</div>
        <span class="pill ${fd.band}">${BAND_LABEL[fd.band]}</span>
      </div>
      <div class="fbody">
      ${steps.length''',
     "finding body wrapper (open)")

swap('''        <h4>Station / engineering</h4><ul>${(STATION_FIX[fd.pdaId]||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      </div></div>`;
  };''',
     '''        <h4>Station / engineering</h4><ul>${(STATION_FIX[fd.pdaId]||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      </div></div></div>`;
  };''',
     "finding body wrapper (close)")

# ---------------------------------------------------------------- blind card
swap('''  const blindCard = res.blind.length ? `<div class="finding gapf">
    <div class="fhead"><div class="ftitle">Demands the HMA does not measure</div><span class="pill gapp">Not measured</span></div>
    <p class="small muted" style="margin:0 0 8px">''',
     '''  const blindCard = res.blind.length ? `<div class="finding gapf">
    <div class="fhead"><div class="ftitle">Demands the HMA does not measure</div><span class="pill gapp">Not measured</span></div>
    <div class="fbody">
    <p class="small muted" style="margin:0 0 8px">''',
     "not-measured card body wrapper (open)")

swap('''      <li>Screen these with the WISHA Hand &amp; Wrist zone in the Ergo Assessment Helper, or a Strain Index analysis in the Task Analysis Scores tool.</li>
    </ul></div></div>` : "";''',
     '''      <li>Screen these with the WISHA Hand &amp; Wrist zone in the Ergo Assessment Helper, or a Strain Index analysis in the Task Analysis Scores tool.</li>
    </ul></div></div></div>` : "";''',
     "not-measured card body wrapper (close)")

# ---------------------------------------------------------------- monitor <details>
swap('''        <summary style="cursor:pointer;font-weight:700">Monitor — ${low.length} lower-ranked match${low.length===1?"":"es"}
          <span class="dim" style="font-weight:400">· click to expand</span></summary>
        <table style="margin-top:10px">''',
     '''        <summary>Monitor — ${low.length} lower-ranked match${low.length===1?"":"es"}</summary>
        <div class="table-wrap"><table>''',
     "monitor summary bar")

swap('''          <td class="dim small">${f.links.linked.map(s=>esc(s.name)).join(", ") || "—"}</td></tr>`).join("")}
        </tbody></table></details>` : "");''',
     '''          <td class="dim small">${f.links.linked.map(s=>esc(s.name)).join(", ") || "—"}</td></tr>`).join("")}
        </tbody></table></div></details>` : "");''',
     "monitor table wrapper")

# ---------------------------------------------------------------- field labels
s = s.replace('<label class="small dim">', '<label class="fieldlabel">')
done.append("  + form labels use the condensed uppercase treatment")

io.open(HTML, "w", encoding="utf8").write(s)
print("Restyled markup:" if s != orig else "No changes needed:")
print("\n".join(done))
