# Paper 1: final quality-control report (round 3)

## 1. Numerical verification
- 75 of 75 headline numbers match the locked outputs (`scripts/final_submission_verification.py`, re-run on this round's files).
- Numbers in the two-column PDF match the manuscript source (word-level number comparison from round 2; the wording edits in this round did not alter any number).
- Figure 1 panel values, Table 2 coefficients and hazard ratios, Table 3 group summaries, Table 4 horizons and Figure 2 numbers-at-risk match their locked source files.

## 2. Page-by-page inspection (rendered)
- **Main PDF (11 pages):** all pages inspected. Title block and abstract on page 1; two-column body; Figure 1 whole on page 4 with caption; Tables 1–4 full width; Figures 2 and 3 full width; references and declarations complete on pages 10–11. No clipped or squeezed content found.
- **Supplementary PDF (10 pages):** all pages inspected. Captions kept with tables. Wide tables readable.
- **Main Word (10 pages in LibreOffice):** Tables 1–4 full width after the section-break fix; no clipped content found. Substitute fonts apply where the named fonts are not installed.
- **Supplementary Word (9 pages in LibreOffice):** full-width tables; narrow numeric columns in S4 and S5 wrap.

## 3. Methodology and scientific integrity
- Model (M2a), cohort, locked results, four tables, three figures and 12 limitations preserved.
- Brier scores: method verified against the code; values unchanged; concern documented separately for supervisor review (`Paper1_Brier_Score_Review_for_Supervisor.md`).
- Missing-data handling verified against the notebook.

## 4. Unresolved (not verified, not changed)
- Ethics approval or exemption, consent-waiver basis and centre-level approvals.
- Authorship: R. Adam's contribution; individual contributions; final approval by all authors.
- Funding and competing-interest statements (from the original draft).
- Registry counts: 63 countries and 242 centres (original text) vs 54 country codes and 288 site codes (extract; 259 sites with eligible patients).
- Predictor measurement time and intended clinical prediction time.
- Brier 5-year value: recompute from raw data before external quotation.
- ASO word-count rule: the 3,500-word count uses the stated method; the official rule is unverified.

## 5. Word count
- Main text: **3,497 words** (Introduction to Conclusions; excludes abstract, tables, legends, declarations and references).
