"""Word version of the supplementary material (same typography as the PDF; full-width tables)."""
import subprocess, re, pathlib
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
ROOT = pathlib.Path("/home/user/LiverMets/manuscript_paper1")
OUT = pathlib.Path(__file__).resolve().parent
src = re.sub(r"^---.*?---\n", "", (ROOT / "Paper1_supplementary.md").read_text(), flags=re.S)
tmp = OUT / "_supp_pandoc.docx"
subprocess.run(["pandoc", "-f", "markdown", "-", "-o", str(tmp), "--resource-path", str(ROOT)], input=src, text=True, check=True)
d = Document(str(tmp))
for s in d.sections:
    s.left_margin = s.right_margin = Pt(44.6); s.top_margin = Pt(56); s.bottom_margin = Pt(52)
    hp = s.header.paragraphs[0]; hp.text = ""
    r = hp.add_run("SURVIVAL PREDICTION IN COLORECTAL LIVER METASTASES  —  SUPPLEMENTARY MATERIAL"); r.font.size = Pt(7); r.bold = True
    r2 = hp.add_run("\tFinal Draft for Supervisor Approval"); r2.font.size = Pt(7); r2.italic = True
for st in ["Normal", "Body Text", "First Paragraph", "Compact"]:
    try:
        d.styles[st].font.name = "Source Serif 4"; d.styles[st].font.size = Pt(9)
    except KeyError:
        pass
body = d.element.body
for tbl in body.iter(qn("w:tbl")):
    tblPr = tbl.find(qn("w:tblPr"))
    for old in tblPr.findall(qn("w:tblW")): tblPr.remove(old)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), "5000"); tw.set(qn("w:type"), "pct"); tblPr.append(tw)
    for r in tbl.iter(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr"); r.insert(0, rPr)
        for old in rPr.findall(qn("w:sz")): rPr.remove(old)
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "15"); rPr.append(sz)
d.save(str(OUT / "Paper1_supplementary_editable.docx")); tmp.unlink()
print("supplementary docx saved")
