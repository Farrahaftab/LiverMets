"""Supplementary material in the same typography as the main manuscript (single full-width column).
Source: manuscript_paper1/Paper1_supplementary.md (built by build_supplementary.py). No content changed."""
import re, subprocess, pathlib
ROOT = pathlib.Path("/home/user/LiverMets/manuscript_paper1")
OUT = pathlib.Path(__file__).resolve().parent
src = (ROOT / "Paper1_supplementary.md").read_text()
src = re.sub(r"^---.*?---\n", "", src, flags=re.S)
body = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"], input=src, capture_output=True, text=True, check=True).stdout
body = re.sub(r'<img src="([^"]+)" style="[^"]*">', r'<img src="\1">', body)
body = re.sub(r"<h1 id=\"[^\"]*\">(.*?)</h1>", r'<h2 class="sec">\1</h2>', body)
body = re.sub(r"<h2 id=\"[^\"]*\">(.*?)</h2>", r'<h3 class="sub">\1</h3>', body)
main_css = (OUT / "build_design.py").read_text()
css = re.search(r'CSS = """(.*?)"""', main_css, re.S).group(1)
css = re.sub(r'\.cols \{[^}]*\}\n', '', css)
css = css.replace(".span { column-span: all; }", "")
css += "\nbody { font-size: 9.2pt; text-align: left; hyphens: manual; }\ntable { font-size: 7.4pt; }\n"
css += ".fig img { width: 92%; }\n.fig { break-inside: avoid; }\n.keep { break-inside: avoid; }\n"
body = re.sub(r'(<p>(?:(?!</p>).)*?</p>)\s*(<table>)', lambda m: '<div class="keep">' + m.group(1) + m.group(2), body, flags=re.S)
body = re.sub(r'(</table>)', r'\1</div>', body)
page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<title>Supplementary material: Paper 1</title><style>{css}</style></head>'
        f'<body><div class="supp">{body}</div></body></html>')
page = page.replace("<h2 class=\"sec\">", "<h2 class=\"sec\" style=\"break-before:auto\">")
(OUT / "Paper1_supp_design.html").write_text(page)
import shutil
for f in (ROOT / "figures").glob("*.png"):
    shutil.copy(f, OUT / "figures" / f.name)
print("supp html written", len(page))
