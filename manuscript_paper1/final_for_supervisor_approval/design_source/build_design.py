"""Two-column main manuscript (HTML for Chromium print), matching the design of the 12-page reference PDF:
Source Serif 4 body, Libre Franklin headings/tables/captions, 0.62 in margins, 0.41 in column gap.
Content comes from manuscript_paper1/Paper1_manuscript.md (built from template_paper1_v2.md). No text is changed here."""
import re, subprocess, html, pathlib, shutil
ROOT = pathlib.Path("/home/user/LiverMets/manuscript_paper1")
OUT = pathlib.Path(__file__).resolve().parent
md = (ROOT / "Paper1_manuscript.md").read_text()
front_md, body_md = md.split("\n# Introduction\n", 1)
body_md = "# Introduction\n" + body_md
title = re.search(r'^title: "(.*)"', front_md, re.M).group(1)
authors = re.search(r"author:\n  - (.*)", front_md).group(1)
def sup(s): return re.sub(r"\^([^^]+)\^", r"<sup>\1</sup>", s)
authors_html = sup(authors.replace("\\*", "*"))
aff_html = sup([l for l in front_md.splitlines() if l.startswith("^1^School")][0])
corr = [l for l in front_md.splitlines() if "Corresponding author" in l][0].replace("\\*", "*")
running = re.search(r"\*\*Running title:\*\* (.*)", front_md).group(1)
synopsis = re.search(r"\*\*Synopsis:\*\* (.*)", front_md).group(1)
abs_block = front_md.split("# Abstract", 1)[1]
def pandoc(txt):
    return subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"], input=txt, capture_output=True, text=True, check=True).stdout
abs_html = pandoc(abs_block)
body_html = pandoc(body_md)
body_html = re.sub(r'<h1 id="[^"]*">(.*?)</h1>', r'<h2 class="sec">\1</h2>', body_html)
body_html = re.sub(r'<h2 id="[^"]*">(.*?)</h2>', r'<h3 class="sub">\1</h3>', body_html)
body_html = re.sub(r'<h1 id="[^"]*">(.*?)</h1>', r'<h2 class="sec">\1</h2>', body_html)
body_html = re.sub(r"<p>\s*<img ([^>]*?)/?>\s*</p>",
                   lambda m: '<div class="span fig%s"><img %s></div>' % (' fig1' if 'Figure1' in m.group(1) else '', m.group(1).strip().rstrip("/")), body_html)
body_html = re.sub(r"<p><strong>(Figure [^<]*)</strong>(.*?)</p>",
                   r'<p class="cap span fcap"><strong>\1</strong>\2</p>', body_html, flags=re.S)
# table captions (source places them after each table) move above the table
cap_re = re.compile(r'\s*<p><strong>(Table \d+)\.</strong>(.*?)</p>', re.S)
tbl_re = re.compile(r'<table>.*?</table>', re.S)
out = []; pos = 0
for m in tbl_re.finditer(body_html):
    out.append(body_html[pos:m.start()])
    tail = body_html[m.end():]
    ca = cap_re.match(tail)
    cap = ''
    end = m.end()
    if ca:
        cap = '<p class="cap span tcap"><strong>%s.</strong>%s</p>' % (ca.group(1), ca.group(2))
        end = m.end() + ca.end()
    out.append('<div class="span tbl">' + cap + m.group(0) + '</div>')
    pos = end
out.append(body_html[pos:])
body_html = ''.join(out)
body_html = body_html.replace('<h2 class="sec">References</h2>\n<ol>', '<h2 class="sec">References</h2>\n<ol class="refs">')
body_html = re.sub(r'(<h2 class="sec">References</h2>\s*)<ol>', r'\1<ol class="refs">', body_html)
body_html = re.sub(r'<img src="([^"]+)" style="[^"]*">', r'<img src="\1">', body_html)
CSS = """
@font-face { font-family: "SS4"; src: url("fonts/source-serif-4-latin-400-normal.woff2") format("woff2"); font-weight: 400; font-style: normal; }
@font-face { font-family: "SS4"; src: url("fonts/source-serif-4-latin-400-italic.woff2") format("woff2"); font-weight: 400; font-style: italic; }
@font-face { font-family: "SS4"; src: url("fonts/source-serif-4-latin-700-normal.woff2") format("woff2"); font-weight: 700; font-style: normal; }
@font-face { font-family: "SS4"; src: url("fonts/source-serif-4-latin-700-italic.woff2") format("woff2"); font-weight: 700; font-style: italic; }
@font-face { font-family: "LF"; src: url("fonts/libre-franklin-latin-400-normal.woff2") format("woff2"); font-weight: 400; font-style: normal; }
@font-face { font-family: "LF"; src: url("fonts/libre-franklin-latin-400-italic.woff2") format("woff2"); font-weight: 400; font-style: italic; }
@font-face { font-family: "LF"; src: url("fonts/libre-franklin-latin-700-normal.woff2") format("woff2"); font-weight: 700; font-style: normal; }
@font-face { font-family: "SS4"; src: url("fonts/source-serif-4-greek-400-normal.woff2") format("woff2"); font-weight: 400; font-style: normal; unicode-range: U+0370-03FF; }
:root { --navy: #1F3A5F; --rule: #c9c2b0; --tint: #f4f1ea; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: "SS4", Georgia, serif; font-size: 9.75pt; line-height: 1.47; color: #1a1a1a; text-align: justify; hyphens: auto; -webkit-hyphens: auto; }
.title { font-family: "SS4", serif; font-weight: 700; font-size: 19.5pt; line-height: 1.2; text-align: center; color: #111; margin: 2px 18px 10px; }
.authors { text-align: center; font-size: 9.8pt; margin: 0 0 5px; }
.aff { font-family: "LF", sans-serif; font-size: 6.9pt; line-height: 1.35; text-align: left; margin: 0 0 6px; color: #333; }
.meta { font-family: "LF", sans-serif; font-size: 7.6pt; line-height: 1.35; margin: 0 0 3px; text-align: left; }
.meta b { color: var(--navy); }
.abstract { background: var(--tint); border-top: 1.2px solid var(--navy); border-bottom: 1.2px solid var(--navy); padding: 8px 13px 7px; margin: 9px 0 11px; }
.abstract h1, .abstract h2 { font-family: "LF", sans-serif; font-weight: 700; font-size: 9.6pt; letter-spacing: .14em; color: var(--navy); margin: 0 0 4px; text-transform: uppercase; }
.abstract p { margin: 0 0 4px; font-size: 8.9pt; line-height: 1.4; text-align: justify; }
.abstract p.kw { font-size: 8pt; margin-top: 4px; }
.cols { column-count: 2; column-gap: 0.41in; column-fill: auto; }
.span { column-span: all; }
h2.sec { font-family: "LF", sans-serif; font-weight: 700; font-size: 10.6pt; letter-spacing: .1em; text-transform: uppercase; color: var(--navy); margin: 12px 0 5px; padding-bottom: 2px; border-bottom: 0.8px solid var(--rule); break-after: avoid; }
h3.sub { font-family: "LF", sans-serif; font-weight: 700; font-size: 9.2pt; color: #111; margin: 7px 0 2px; break-after: avoid; }
p { margin: 0 0 5px; orphans: 2; widows: 2; }
.cols > p:first-child, .cols > h2:first-child { margin-top: 0; }
table { width: 100%; border-collapse: collapse; font-family: "LF", sans-serif; font-size: 7.6pt; line-height: 1.32; margin: 2px 0 6px; break-inside: avoid; }
th, td { padding: 3px 5px; vertical-align: top; text-align: right; border-bottom: 0.4px solid #d8d2c4; }
th { font-weight: 700; color: #111; border-top: 1.1px solid var(--navy); border-bottom: 0.8px solid var(--navy); }
td:first-child, th:first-child { text-align: left; }
tbody tr:last-child td { border-bottom: 1.1px solid var(--navy); }
.tbl { break-inside: avoid; }
.cap { font-family: "LF", sans-serif; font-size: 7.9pt; line-height: 1.35; text-align: left; margin: 6px 0 3px; }
.cap strong { color: var(--navy); }
.tcap { break-after: avoid; }
.fig { break-inside: avoid; text-align: center; margin: 6px 0 2px; }
.fig img { width: 100%; height: auto; }
.fig.fig1 img { width: 4.4in; }
.fcap { margin-top: 2px; font-family: "SS4", serif; font-size: 8.4pt; line-height: 1.38; text-align: justify; }
.fcap strong { font-family: "LF", sans-serif; color: var(--navy); }
ol.refs { font-size: 7.9pt; line-height: 1.36; padding-left: 15px; margin: 0 0 4px; text-align: left; }
ol.refs li { margin-bottom: 2px; }
a { color: var(--navy); }
"""
front = f"""
<div class="span">
 <div class="title">{html.escape(title)}</div>
 <p class="authors">{authors_html}</p>
 <p class="aff">{aff_html}</p>
 <p class="meta">{corr.replace('*Corresponding', '<i>Corresponding').replace('MSc — ', 'MSc</i> — ')}</p>
 <p class="meta"><b>Running title:</b> {running}</p>
 <p class="meta"><b>Synopsis:</b> {synopsis}</p>
 <div class="abstract">{abs_html}</div>
</div>
"""
page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Prognostic Survival Prediction in Colorectal Liver Metastases</title><style>{CSS}</style></head>'
        f'<body><div class="front">{front}</div><div class="cols">{body_html}</div></body></html>')
(OUT / "Paper1_main_design.html").write_text(page)
(OUT / "figures").mkdir(exist_ok=True)
for f in (ROOT / "figures").glob("*.png"):
    shutil.copy(f, OUT / "figures" / f.name)
print("html written")
