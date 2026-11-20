"""Editable Word version of the two-column main manuscript.
Body text is in two columns; tables and figures (and their captions) are full width,
using continuous section breaks. Content is taken from Paper1_manuscript.md via pandoc."""
import copy, subprocess, pathlib, re
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt
ROOT = pathlib.Path("/home/user/LiverMets/manuscript_paper1")
OUT = pathlib.Path(__file__).resolve().parent
tmp = OUT / "_pandoc_main.docx"
subprocess.run(["pandoc", str(ROOT / "Paper1_manuscript.md"), "-o", str(tmp), "--resource-path", str(ROOT)], check=True)
doc = Document(str(tmp))
body = doc.element.body
final_sect = body.find(qn("w:sectPr"))
def sect_para(cols):
    p = OxmlElement("w:p"); pPr = OxmlElement("w:pPr")
    sp = copy.deepcopy(final_sect)
    for ch in list(sp):
        if ch.tag in (qn("w:headerReference"), qn("w:footerReference")):
            sp.remove(ch)
    for old in sp.findall(qn("w:cols")): sp.remove(old)
    typ = sp.find(qn("w:type"))
    if typ is None:
        typ = OxmlElement("w:type"); sp.insert(0, typ)
    typ.set(qn("w:val"), "continuous")
    c = OxmlElement("w:cols"); c.set(qn("w:num"), str(cols)); c.set(qn("w:space"), "360")
    sp.append(c)
    pPr.append(sp); p.append(pPr); return p
def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))
kids = list(body)
# 1. move "Table N." captions above the table they follow
for i, el in enumerate(list(body)):
    if el.tag == qn("w:p") and re.match(r"^Table \d+\.", text_of(el)) and i > 0 and body[list(body).index(el) - 1].tag == qn("w:tbl"):
        tbl = body[list(body).index(el) - 1]
        tbl.addprevious(el)
# 2. wrap front matter, full-width items; body two-column from Introduction
kids = list(body)
intro_idx = next(i for i, el in enumerate(kids) if el.tag == qn("w:p") and text_of(el).strip() == "Introduction")
kids[intro_idx].addprevious(sect_para(1))
def is_full(el):
    if el.tag == qn("w:tbl"): return True
    if el.tag != qn("w:p"): return False
    if el.find(".//" + qn("w:drawing")) is not None: return True
    return bool(re.match(r"^(Table|Figure) \d+\.", text_of(el)))
snapshot = list(body)
groups = []
i = intro_idx + 1
while i < len(snapshot):
    el = snapshot[i]
    if el is final_sect: break
    if el.tag == qn("w:p") and text_of(el).strip() == "References": break
    if is_full(el):
        first = el; last = el
        if el.tag == qn("w:p") and re.match(r"^Table \d+\.", text_of(el)) and i + 1 < len(snapshot) and snapshot[i+1].tag == qn("w:tbl"):
            last = snapshot[i+1]; i += 1
        elif el.tag == qn("w:p") and el.find(".//" + qn("w:drawing")) is not None and i + 1 < len(snapshot) and re.match(r"^Figure \d+\.", text_of(snapshot[i+1])):
            last = snapshot[i+1]; i += 1
        groups.append((first, last))
    i += 1
for first, last in groups:
    first.addprevious(sect_para(1))
    last.addnext(sect_para(2))
# 2b. full-width tables: set table width to 100% of the text block with a wider first column
TEXT_TW = 10454  # 7.26 in in twips
for tbl in body.iter(qn("w:tbl")):
    tblPr = tbl.find(qn("w:tblPr"))
    for old in tblPr.findall(qn("w:tblW")): tblPr.remove(old)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), "5000"); tw.set(qn("w:type"), "pct"); tblPr.append(tw)
    for old in tblPr.findall(qn("w:tblLayout")): tblPr.remove(old)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = tbl.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol")) if grid is not None else []
    n = len(cols)
    if n:
        first = int(TEXT_TW * (0.30 if n > 4 else 0.40))
        rest = (TEXT_TW - first) // (n - 1) if n > 1 else 0
        widths = [first] + [rest] * (n - 1)
        for gc, w in zip(cols, widths): gc.set(qn("w:w"), str(w))
        for tr in tbl.iter(qn("w:tr")):
            for k, tc in enumerate(tr.findall(qn("w:tc"))):
                tcPr = tc.find(qn("w:tcPr"))
                if tcPr is None:
                    tcPr = OxmlElement("w:tcPr"); tc.insert(0, tcPr)
                for old in tcPr.findall(qn("w:tcW")): tcPr.remove(old)
                tcw = OxmlElement("w:tcW"); tcw.set(qn("w:w"), str(widths[min(k, n-1)])); tcw.set(qn("w:type"), "dxa"); tcPr.insert(0, tcw)
    for r in tbl.iter(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr"); r.insert(0, rPr)
        for old in rPr.findall(qn("w:sz")): rPr.remove(old)
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "15"); rPr.append(sz)
# last section (References etc.) stays two-column via final sectPr
for sp in body.iter(qn("w:sectPr")):
    if sp is final_sect:
        cols = sp.find(qn("w:cols"))
        if cols is None:
            cols = OxmlElement("w:cols"); sp.append(cols)
        cols.set(qn("w:num"), "2"); cols.set(qn("w:space"), "360")
        t = sp.find(qn("w:type"))
        if t is None:
            t = OxmlElement("w:type"); sp.insert(0, t)
        t.set(qn("w:val"), "continuous")
# 3. running header and page-number footer (first section; later sections inherit)
sec0 = doc.sections[0]
sec0.left_margin = sec0.right_margin = Pt(44.6)
sec0.top_margin = Pt(56); sec0.bottom_margin = Pt(52)
hp = sec0.header.paragraphs[0]; hp.text = ""
r = hp.add_run("SURVIVAL PREDICTION IN COLORECTAL LIVER METASTASES"); r.font.size = Pt(7); r.bold = True
r2 = hp.add_run("\tFinal Draft for Supervisor Approval"); r2.font.size = Pt(7); r2.italic = True
fp = sec0.footer.paragraphs[0]; fp.alignment = 1
def field(par, instr):
    r = par.add_run(); f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin"); r._r.append(f1)
    r = par.add_run(); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr; r._r.append(it)
    r = par.add_run(); f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "separate"); r._r.append(f2)
    par.add_run("1")
    r = par.add_run(); f3 = OxmlElement("w:fldChar"); f3.set(qn("w:fldCharType"), "end"); r._r.append(f3)
rr = fp.add_run("Page "); rr.font.size = Pt(7)
field(fp, " PAGE "); rr = fp.add_run(" of "); rr.font.size = Pt(7); field(fp, " NUMPAGES ")
for run in fp.runs: run.font.size = Pt(7)
# 4. font defaults for body
st = doc.styles["Normal"]; st.font.name = "Cambria"; st.font.size = Pt(9.5)
doc.save(str(OUT / "Paper1_main_design_editable.docx"))
tmp.unlink()
print("saved")
