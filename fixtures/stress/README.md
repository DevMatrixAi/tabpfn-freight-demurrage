# Stress fixtures (demurrage spine)

`missing_wide_demurrage.csv` — ~20 rows from freight-demurrage with:
- elevated missingness on notes / dwell / free days / cargo value
- 40+ synthetic `noise_f*` columns (wide-table stress; shape[1] >= 50)

The CSV is checked in as plain text. To rebuild it deterministically, run:
`python fixtures/stress/_unpack_missing_wide.py`

Use with mock eval / ablations to show TabPFN-3.5 data-as-is (missing + wide)
without claiming live BeyondArena scores.
