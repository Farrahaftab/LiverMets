"""Rebuild the 12-page two-column design of Paper 1 (main manuscript) as HTML for Chromium print.
Source: manuscript_paper1/Paper1_manuscript.md (generated from template_paper1_v2.md).
Visual reference: the uploaded 12-page PDF (browser print). No text is changed by this script."""
import re, subprocess, html, sys, pathlib
ROOT = pathlib.Path("/home/user/LiverMets/manuscript_paper1")
OUT = pathlib.Path(__file__).resolve().parent
md = (ROOT / "Paper1_manuscript.md").read_text()
front_md, body_md = md.split("\n# Introduction\n", 1)
body_md = "# Introduction\n" + body_md
# authors, affiliations, corresponding author, running title, synopsis, abstract come from the front matter
title = re.search(r'^title: "(.*)"', front_md, re.M).group(1)
authors = re.search(r"author:\n  - (.*)", front_md).group(1)
def sup(s): return re.sub(r"\^([^^]+)\^", r"<sup>\1</sup>", s)
authors_html = sup(authors.replace("\\*", "*")).replace("<sup>1,*</sup>", "<sup>1,*</sup>")
aff = [l for l in front_md.splitlines() if l.startswith("^1^School")][0]
aff_html = sup(aff)
corr = [l for l in front_md.splitlines() if "Corresponding author" in l][0].replace("\\*", "*")
running = re.search(r"\*\*Running title:\*\* (.*)", front_md).group(1)
synopsis = re.search(r"\*\*Synopsis:\*\* (.*)", front_md).group(1)
abs_block = front_md.split("# Abstract", 1)[1]
abs_html = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"], input=abs_block, capture_output=True, text=True, check=True).stdout
body_html = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"], input=body_md, capture_output=True, text=True, check=True).stdout
# headings
body_html = re.sub(r"<h1 id=\"[^\"]*\">(.*?)</h1>", r'<h2 class="sec">\1</h2>', body_html)
body_html = re.sub(r"<h2 id=\"[^\"]*\">(.*?)</h2>", r'<h3 class="sub">\1</h3>', body_html)
# figures: image paragraphs become full-width blocks
body_html = re.sub(r"<p>\s*<img ([^>]*?)/?>\s*</p>", lambda m: '<div class="span fig"><img %s></div>' % m.group(1).strip().rstrip("/"), body_html)
# captions: figure captions stay below; table captions move above the table
body_html = re.sub(r"<p><strong>(Figure [^<]*)</strong>(.*?)</p>", r'<p class="cap span fcap"><strong>\1</strong>\2</p>', body_html, flags=re.S)
tbl_re = re.compile(r'<table>.*?</table>', re.S)
cap_after = re.compile(r'\s*<p class="cap span tcap"><strong>(Table \d+)\.</strong>(.*?)</p>', re.S)
def tblrep(m):
    tbl = m.group(0)
    tail = body_html[m.end():]
    ca = cap_after.match(tail)
    if ca:
        pending_cap.append(ca.end())
        capfix = '<p class="cap span tcap"><strong>%s.</strong>%s</p>' % (ca.group(1), ca.group(2))
        return '<div class="span tbl">' + capfix + tbl + '</div>'
    return '<div class="span tbl">' + tbl + '</div>'
pending_cap = []
# Pass 1: captions that follow a table are moved above it and removed from after it.
out = []; pos = 0
for m in tbl_re.finditer(body_html):
    out.append(body_html[pos:m.start()])
    tail = body_html[m.end():]
    ca = cap_after.match(tail)
    cap = ''
    if ca:
        cap = '<p class="cap span tcap"><strong>%s.</strong>%s</p>' % (ca.group(1), ca.group(2))
        end = m.end() + ca.end()
    else:
        end = m.end()
    out.append('<div class="span tbl">' + cap + m.group(0) + '</div>')
    pos = end
out.append(body_html[pos:])
body_html = ''.join(out)
# references list to its own block (keeps two columns)
body_html = body_html.replace("<ol>", '<ol class="refs">', 1) if "<h3" not in body_html.split("Reference")[-1][:0] else body_html
css = """
@page { size: Letter; }
:root { --navy:#1F3A5F; --rule:#c9c2b0; --tint:#f4f1ea; }
* { box-sizing: border-box; }
body { font-family: "Caladea", "Cambria", serif; font-size: 10.6pt; line-height: 1.56; color:#1a1a1a; text-align: justify; hyphens: auto; margin:0; }
.title { font-family: "Carlito", "Calibri", sans-serif; font-weight:700; font-size: 19.5pt; line-height:1.18; text-align:center; color:#111; margin: 4px 24px 12px; }
.authors { text-align:center; font-size:9.6pt; margin:0 0 6px; }
.aff { font-size:7.4pt; line-height:1.3; text-align:left; margin:0 0 6px; color:#333; }
.meta { font-size:8pt; margin:0 0 3px; }
.meta b { font-family:"Carlito", sans-serif; color:var(--navy); }
.abstract { background: var(--tint); border-top: 1.2px solid var(--navy); border-bottom: 1.2px solid var(--navy); padding: 9px 14px 7px; margin: 10px 0 12px; text-align: justify; }
.abstract h1, .abstract h2 { font-family:"Carlito", sans-serif; font-size:10.5pt; letter-spacing:.14em; color:var(--navy); margin:0 0 5px; text-transform:uppercase; }
.abstract p { margin:0 0 4px; font-size:9.6pt; line-height:1.4; }
.abstract p.kw { font-size:8.2pt; margin-top:5px; }
.cols { column-count: 2; column-gap: 0.36in; column-fill: auto; }
.span { column-span: all; }
h2.sec { font-family:"Carlito", "Calibri", sans-serif; font-weight:700; font-size: 11pt; letter-spacing:.12em; text-transform:uppercase; color:var(--navy); margin: 13px 0 5px; padding-bottom:2px; border-bottom:0.8px solid var(--rule); break-after: avoid; column-span: none; }
h3.sub { font-family:"Carlito", sans-serif; font-weight:700; font-size: 9.9pt; color:#111; margin: 7px 0 2px; break-after: avoid; }
p { margin: 0 0 5px; orphans: 2; widows: 2; }
.cols > p:first-child, .cols > h2:first-child { margin-top:0; }
table { width:100%; border-collapse: collapse; font-family:"Carlito", "Calibri", sans-serif; font-size: 8.2pt; line-height:1.3; margin: 2px 0 8px; break-inside: avoid; }
th, td { padding: 2.2px 4px; vertical-align: top; text-align: right; border-bottom: 0.4px solid #d8d2c4; }
th { font-weight:700; color:#111; border-top:1.1px solid var(--navy); border-bottom:0.8px solid var(--navy); }
td:first-child, th:first-child { text-align:left; }
tbody tr:last-child td { border-bottom: 1.1px solid var(--navy); }
.tbl { break-inside: avoid; }
.cap { font-family:"Carlito", sans-serif; font-size: 8.4pt; line-height:1.3; text-align:left; margin: 6px 0 3px; }
.cap strong { color:var(--navy); }
.tcap { break-after: avoid; }
.fig { break-inside: avoid; text-align:center; margin: 6px 0 2px; }
.fig img { width: 100%; max-width: 100%; height:auto; }
.fcap { margin-top: 2px; }
ol.refs, ol { font-size: 8.4pt; line-height:1.38; padding-left: 16px; margin: 0 0 4px; text-align:left; }
ol.refs li { margin-bottom: 2px; }
.decl p { font-size: 8.6pt; }
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
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Prognostic Survival Prediction in Colorectal Liver Metastases</title><style>{css}</style></head>
<body><div class="front">{front}</div><div class="cols">{body_html}</div></body></html>"""
(OUT / "Paper1_main_design.html").write_text(page)
import shutil
(OUT / "figures").mkdir(exist_ok=True)
for f in (ROOT / "figures").glob("*.png"):
    shutil.copy(f, OUT / "figures" / f.name)
print("html written", len(page))
