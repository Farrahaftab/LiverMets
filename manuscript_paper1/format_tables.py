"""Post-processes the Word documents: fixed column widths sized to content, 8 pt table text.
Cell text is not changed. Usage: python format_tables.py file.docx [more.docx ...]"""
import sys
from docx import Document
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TEXT_WIDTH_IN = 6.5          # Letter page, 1-inch side margins (pandoc default reference document)
MIN_CHARS = 8


def set_fixed_layout(table):
    tblPr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    for el in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(el)
    tblPr.append(layout)


def format_table(table):
    ncol = len(table.columns)
    header = [c.text for c in table.rows[0].cells]
    body = [[c.text for c in r.cells] for r in table.rows[1:]]
    weights = []
    for j in range(ncol):
        words = header[j].split() or [""]
        longest_word = max(len(w) for w in words)
        longest_cell = max([len(r[j]) for r in body if j < len(r)] + [0])
        weights.append(max(MIN_CHARS, longest_word + 2, min(longest_cell, 34)))
    total = float(sum(weights))
    widths = [Inches(TEXT_WIDTH_IN * w / total) for w in weights]
    set_fixed_layout(table)
    table.autofit = False
    for row in table.rows:
        for j, cell in enumerate(row.cells):
            cell.width = widths[j]
            for par in cell.paragraphs:
                for run in par.runs:
                    run.font.size = Pt(8)
    for j, col in enumerate(table.columns):
        col.width = widths[j]


def main(paths):
    for path in paths:
        doc = Document(path)
        for t in doc.tables:
            format_table(t)
        doc.save(path)
        print(f"{path}: formatted {len(doc.tables)} tables")


if __name__ == "__main__":
    main(sys.argv[1:])
