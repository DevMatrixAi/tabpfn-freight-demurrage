# Stress fixtures (demurrage spine)

`missing_wide_demurrage.csv` — 200 rows from freight-demurrage with:
- elevated missingness on notes / dwell / free days / cargo value
- 40 synthetic `noise_f*` columns (wide-table stress)

Use with mock eval / ablations to show TabPFN-3.5 “data as-is” story
(missing values + wide tables) without claiming live BeyondArena scores.
