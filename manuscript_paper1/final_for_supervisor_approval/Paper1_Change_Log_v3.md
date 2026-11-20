# Paper 1: change log (round 3)

Scope: wording, reference, layout and presentation. The locked v8 Cox model (M2a), the 17,262-patient cohort (8,463 development; 8,799 validation), all numerical results, the four tables, the three main figures, the 12 limitations and the conclusions are unchanged. No analysis was rerun.

## 1. Word count reduced to 3,497 (limit 3,500)
- Counting rule used: Introduction to Conclusions, excluding abstract, tables, figure legends, declarations and references (the rule in `build_paper1.py`). **ASO's official counting rules could not be verified from this environment**; please confirm against the current instructions.
- Edits (wording only, no content removed): aims paragraph condensed; analysis-software sentence shortened; excluded-patient paragraph condensed; calibration and Discussion paragraphs condensed; earlier-analysis sentence condensed; study-population sentence condensed; missing-data sentence condensed (same meaning).
- Kept in full: all 12 limitations, predictor-timing paragraph, missing-data handling, sensitivity analyses, Brier method, and the conclusions.

## 2. Reference 3 restored (user-verified)
Viganò L, Risi L, Ragaini E, Ieva F, Desiato E. Prognostic scores for liver resection in colorectal metastases: performance, limitations, and methodological pitfalls—a systematic review and meta-analysis. *Cancers*. 2026;18(4):625. doi:10.3390/cancers18040625. Verified from the publisher by the authors (per the request); not re-checked in this environment.

## 3. Brier scores
- Locked values unchanged. The method (IPCW, training censoring distribution, time grid) is stated in Methods; Table 4 carries a caution for the 5-year value.
- The concern is documented separately for supervisor review in `Paper1_Brier_Score_Review_for_Supervisor.md`. It is not a claimed calculation error.

## 4. Design
- Main manuscript rebuilt to match the reference PDF: Source Serif 4 body at 9.75 pt, Libre Franklin headings, captions and tables, 1.47 line spacing, 0.41 in column gap, 0.62 in margins, running header and "Page x of y" footer. Output is **11 pages** (reference: 12); the difference comes from pagination, not from removed content.
- Figure 1 set at 4.4 in wide so the whole flow chart fits on one page with its caption (previously split across pages).
- Table 1 caption placed above its table; Tables 1–4 and Figures 2–3 span full width; no clipped content.

## 5. Word document
- Two-column main text with full-width tables and figures, built with continuous section breaks. The section-break order was corrected in this round: text before a full-width item is two-column; the item itself is one-column. Tables 1–4 now span the full text width.
- Fonts: Source Serif 4 and Libre Franklin are named in the document. **If they are not installed, Word substitutes other fonts, so line breaks will differ from the PDF.** Narrow numeric columns in supplementary Tables S4 and S5 wrap in the Word render.

## 6. Supplementary
- Same typography and header/footer as the main manuscript, in one full-width column (10 pages PDF; 9 pages Word). Captions are kept with their tables.
- Content unchanged from the build of `Paper1_supplementary.md`.

## 7. Missing-data wording (approved in round 2, carried forward)
- Methods and Limitation 5 describe the same handling, confirmed in the notebook: indicators plus development-median single imputation for interval, count and size; multiple imputation only in the CEA sensitivity analysis.

## Not changed (deliberately)
- No refit, recalibration or new analysis.
- Ethics, consent, authorship, registry counts and predictor timing remain marked as unresolved (see the one-page outstanding-issues summary).
