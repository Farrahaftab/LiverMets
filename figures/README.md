# STROBE Flow Diagram — Publication-Ready Versions

## Quick Start

This directory contains **two complementary, publication-ready versions** of the STROBE patient flow diagram for the LiverMets CRLM Prognostic Phenotyping Study, with all 9 ASO peer review recommendations implemented.

### Files

| File | Format | Best For | Instructions |
|------|--------|----------|--------------|
| `STROBE_Figure_1_ASO_Revised.html` | Interactive HTML5 | Digital journals, online presentations, web publishing | Open in any web browser. Self-contained (no dependencies). |
| `strobe_diagram_aso_revised.py` | Python/Matplotlib | Print journals, high-res PDFs, supplementary figures | `python strobe_diagram_aso_revised.py` → generates `STROBE_Flow_Diagram_ASO_Revised.png` (310 dpi) |
| `ASO_REVISIONS_SUMMARY.md` | Documentation | Understanding changes, submission checklist | Read for detailed before/after comparison of all 9 improvements |

---

## Recommended Usage

### For Journal Submission (Annals of Surgical Oncology)
1. Run Python script to generate high-res PNG: `python strobe_diagram_aso_revised.py`
2. Include generated PNG file in manuscript supplementary materials or inline
3. Copy caption text from file header into figure legend in manuscript:
   > **Figure 1.** STROBE flow diagram illustrating patient selection from the LiverMetSurvey International Registry, cohort derivation, CART-based prognostic phenotyping, treatment stratification, and statistical analyses...

### For Online Presentations / Webinars
1. Open `STROBE_Figure_1_ASO_Revised.html` in web browser
2. Screenshot at desired resolution or embed directly in web presentation
3. Responsive design adapts to any screen size

### For PDF Reports / Theses
1. Run Python script to generate PNG: `python strobe_diagram_aso_revised.py`
2. Insert PNG into document at 300 dpi (print quality)
3. Use figure caption from Python script comments

---

## Key Features

✅ **All 9 ASO Recommendations Implemented:**
- Simplified CART methodology (no hyperparameters in diagram)
- Streamlined statistical methods box
- Bulleted key findings (instead of dense paragraph)
- Increased font sizes for print readability (20-30% boost)
- Consistent red exclusion boxes throughout
- No legend (self-evident colour scheme)
- Uniform PSM box colours (no misleading highlights)
- Larger footnote/abbreviation text
- Journal-style "Figure 1" caption

✅ **Publication-Ready Quality:**
- All numerical values verified against live Colab execution
- 310 dpi PNG output suitable for journal submission
- Responsive HTML works on all devices
- No external dependencies (self-contained files)

✅ **Reproducible & Version-Controlled:**
- Python script generates identical PNG every time
- All values hardcoded and documented
- No manual Illustrator edits or fragile design files

---

## Figure Values at a Glance

**Cohort Flow (n=29,565 → 14,759)**
- Registry: 29,565 patients, 63 countries
- After TNM filter: 19,465 (excluded 10,100 incomplete TNM)
- After survival/vital status filter: 14,759 (excluded 4,706)

**Phenotype Distribution**
- **Favourable:** 3,953 (26.8%), median OS 6.49 yrs
- **Intermediate:** 2,666 (18.1%), median OS 5.55 yrs  
- **Adverse:** 8,140 (55.2%), median OS 4.06 yrs

**Statistical Significance**
- Global OS log-rank χ²(2)=224.89, p<0.001
- Global RFS log-rank χ²(2)=371.66, p<0.001
- Multivariable Cox: Adverse HR=1.616 (p<0.001), C-index=0.607

---

## Technical Details

### HTML Version
- **File size:** ~16 KB
- **Dependencies:** None (self-contained CSS/HTML)
- **Compatibility:** All modern browsers (Chrome, Firefox, Safari, Edge)
- **Customization:** Edit CSS in `<style>` block for colour/font changes
- **Theme support:** Automatically adapts to browser light/dark mode

### Python Version
- **Dependencies:** `matplotlib`, `numpy` (standard scientific stack)
- **Output:** PNG at 310 dpi (suitable for print journals)
- **Customization:** Edit constants at top for different values, or modify `rbox()` function for layout changes
- **Runtime:** ~5 seconds to generate and display PNG

---

## Verification

All numerical values are hardcoded at the top of the Python script and correspond exactly to:
- **Live Colab notebook execution** (verified July 13, 2026)
- **PSM output CSV files**
- **Temporal validation analysis**
- **Multivariable Cox regression results**

No values are computed dynamically—all are static and locked for reproducibility.

---

## Submission Checklist

- [ ] Generated high-res PNG from Python script (or use HTML version for online journals)
- [ ] Verified figure caption matches manuscript text
- [ ] Checked all numerical values against Colab execution
- [ ] Confirmed 310 dpi resolution for print submission
- [ ] Copied caption text to manuscript Figure 1 legend
- [ ] Tested HTML version in target browser(s) if using digital submission

---

## Questions or Customization?

See `ASO_REVISIONS_SUMMARY.md` for:
- Detailed before/after comparison of all 9 changes
- Font size increases with quantification
- Colour scheme documentation
- Submission status and next steps

---

**Status:** ✅ Ready for submission to Annals of Surgical Oncology  
**Last Updated:** July 13, 2026  
**Branch:** `claude/code-review-outputs-r2xcwy`
