"""Finalises the supervisor-review Word documents and builds the combined PDF.
- running header and page-numbered footer (review-draft format of the reference manuscript)
- table column widths and 8 pt table text (format_tables.py)
- main and supplementary documents converted to PDF and merged into one review PDF
Cell text and every number are not changed by this script."""
import copy, subprocess, sys
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
sys.path.insert(0, str(Path(__file__).resolve().parent))
from format_tables import format_table

HERE = Path(__file__).resolve().parent
HEADER = "LIVERMETS | COLORECTAL LIVER METASTASES | SUPERVISOR REVIEW"
FOOTER = "CONFIDENTIAL REVIEW DRAFT • PAGE "


def add_field(paragraph, instr):
    run = paragraph.add_run()
    for tag, text in [("begin", None), ("instr", instr), ("separate", None), ("text", "1"), ("end", None)]:
        if tag == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
            run._r.append(el)
        elif tag == "text":
            el = OxmlElement("w:t")
            el.text = text
            run._r.append(el)
        else:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), {"begin": "begin", "separate": "separate", "end": "end"}[tag])
            run._r.append(el)
    run.font.size = Pt(7.5)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def style_par(par, text=None, align=WD_ALIGN_PARAGRAPH.LEFT):
    if text is not None:
        run = par.add_run(text)
        run.font.size = Pt(7.5)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    par.alignment = align


def finalise(path):
    doc = Document(path)
    for section in doc.sections:
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False
        hp = section.header.paragraphs[0] if section.header.paragraphs else section.header.add_paragraph()
        hp.text = ""
        style_par(hp, HEADER, WD_ALIGN_PARAGRAPH.LEFT)
        fp = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
        fp.text = ""
        style_par(fp, FOOTER, WD_ALIGN_PARAGRAPH.CENTER)
        add_field(fp, "PAGE")
    for t in doc.tables:
        format_table(t)
    doc.save(path)
    return len(doc.tables)


def to_pdf(docx_path):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(HERE), str(docx_path)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    return HERE / (Path(docx_path).stem + ".pdf")


if __name__ == "__main__":
    main_docx = HERE / "Paper1_manuscript.docx"
    supp_docx = HERE / "Paper1_supplementary.docx"
    for d in (main_docx, supp_docx):
        n = finalise(d)
        print(f"{d.name}: header/footer set; {n} tables formatted")
    p1 = to_pdf(main_docx)
    p2 = to_pdf(supp_docx)
    combined = HERE / "Paper1_Full_Manuscript_Supervisor_Review.pdf"
    subprocess.run(["pdfunite", str(p1), str(p2), str(combined)], check=True)
    print("combined PDF:", combined)
