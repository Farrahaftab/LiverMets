# Running the Figure 1 generator in Google Colab

The generator needs only Python and matplotlib. It reads the locked output CSVs from the repository.

## Option A: clone the repository (simplest)

Open a new notebook at <https://colab.research.google.com> and run these cells.

```python
# Cell 1: get the repository (the locked outputs are committed in it)
!git clone https://github.com/Farrahaftab/LiverMets.git
%cd LiverMets
```

```python
# Cell 2: matplotlib is pre-installed in Colab; this line only confirms the version
import matplotlib; print(matplotlib.__version__)
```

```python
# Cell 3: generate the figure, the caption and the verification report
!python figures/figure1_strobe_v9/make_figure1_strobe.py
```

```python
# Cell 4: view the PNG and download the outputs
from IPython.display import Image, display
display(Image("results/final_v9/figure1/Figure1_STROBE_Cox.png", width=600))

from google.colab import files
for f in ["Figure1_STROBE_Cox.png", "Figure1_STROBE_Cox.pdf", "Figure1_STROBE_Cox.svg",
          "Figure1_caption.md", "verification_report.md", "verification_report.csv"]:
    files.download(f"results/final_v9/figure1/{f}")
```

If the repository is private, Colab must be authorised for GitHub (use the Colab "Secrets" panel to add a personal access token, then `!git clone https://<token>@github.com/Farrahaftab/LiverMets.git`). Do not paste the token into a shared notebook.

## Option B: upload the source folders (no git)

1. In Colab, open the file panel and upload a zip of the repository, or upload these folders: `results/final_v7/`, `results/final_v9/paper1/` and `figures/figure1_strobe_v9/`.
2. Keep the same relative layout: `figures/figure1_strobe_v9/make_figure1_strobe.py` must sit two levels below the folder that contains `results/`.
3. Run `!python figures/figure1_strobe_v9/make_figure1_strobe.py` from that folder.

## Expected result

* Console output: `27 checks passed, 1 discrepancy(ies) reported` (the discrepancy is the F02 / F02b C-index CI; see `verification_report.md`).
* Files in `results/final_v9/figure1/`.

If any check reports FAIL, the figure is not drawn. Read `verification_report.md`, which names the failed check, before doing anything else.

## Environment notes

* Fonts: DejaVu Sans is bundled with matplotlib, so the figure renders identically in Colab and locally.
* The PNG is 4320 px wide (600 dpi at 7.2 in). The PDF and SVG are vector files for the journal.
