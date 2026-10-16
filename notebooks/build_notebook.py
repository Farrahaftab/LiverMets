"""Convert the cell-marked source (livermets_survival_colab.py) into a Jupyter/Colab notebook.

Usage: python build_notebook.py livermets_survival_colab.py LiverMets_PhD_Survival_Analysis.ipynb
"""
import re
import sys

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

src_path, out_path = sys.argv[1], sys.argv[2]
cells, kind, buf = [], None, []
for line in open(src_path, encoding='utf-8').read().split('\n'):
    m = re.match(r'# %% \[(markdown|code)\]', line)
    if m:
        if kind is not None:
            cells.append((kind, buf))
        kind, buf = m.group(1), []
    else:
        buf.append(line)
if kind is not None:
    cells.append((kind, buf))

nb = new_notebook()
for kind, lines in cells:
    if kind == 'markdown':
        text = []
        for l in lines:
            if l == '#':
                text.append('')
            elif l.startswith('# '):
                text.append(l[2:])
            else:
                text.append(l)
        nb.cells.append(new_markdown_cell('\n'.join(text).strip('\n')))
    else:
        nb.cells.append(new_code_cell('\n'.join(lines).strip('\n')))

nb.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb.metadata['language_info'] = {'name': 'python'}
nbformat.write(nb, out_path)
print(f'Wrote {out_path}: {len(nb.cells)} cells ({sum(c.cell_type == "code" for c in nb.cells)} code)')
