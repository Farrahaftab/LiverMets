# Paper 1: verification report (round 4)

## 1. Numbers
- 75 of 75 headline checks pass against the locked outputs (`scripts/final_submission_verification.py`).
- The corrected labels contain no numerical change. S2f and S7 values match the locked files (F34; F25).

## 2. Labels
- The four searched labels no longer appear in the main or supplementary PDF or Word text.
- Corrected labels are present in S2f (title and rows), S7, and the main-text Participants paragraph.

## 3. Brier scores
- Method verified against the notebook (`brier_score(y_tr, y_va, S[va][:, 2:], TB)`) and against the installed scikit-survival 0.28.0 source (IPCW; training censoring distribution; at-risk and event weights).
- Values (0.0604, 0.101, 0.0651) cannot be recomputed here: patient-level data and raw workbooks are not in the repository or this environment.
- An illustrative simulation with the true survival function showed that the same estimator can give a 5-year value below the 3-year value under heavy censoring, so non-monotonicity alone is not evidence of error.
- Result: **no demonstrated calculation error; values unchanged; the check is documented for supervisor review.**

## 4. Layout and readability
- Main PDF: 11 pages, two-column design unchanged; Word: two-column text, full-width tables and figures (LibreOffice render; fonts substituted if Source Serif 4 and Libre Franklin are not installed).
- Supplementary PDF: 10 pages; Word: 9 pages (LibreOffice render).
- Changed supplementary pages 2 and 7 checked visually for clipping.

## 5. Unresolved (not verified, not changed)
- Ethics approval or exemption, consent-waiver basis, centre-level approvals.
- Authorship: R. Adam's contribution; individual contributions; final approval by all authors.
- Funding and competing-interest statements (from the original draft).
- Registry counts: 63 countries and 242 centres (original text) vs 54 country codes and 288 site codes (extract; 259 sites with eligible patients).
- Predictor measurement time and intended clinical prediction time.
- 5-year Brier value: recompute from raw data before quoting outside the manuscript.
- ASO word-count rule: 3,498 words by the stated method; official rule unverified.

## 6. Word count
- Main text: **3,498 words** (Introduction to Conclusions; excludes abstract, tables, legends, declarations and references).
