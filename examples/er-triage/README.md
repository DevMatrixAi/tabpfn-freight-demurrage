# Example domain pack: synthetic ER intake triage

**Optional** narrative pack for `tabpfn-hack-core`. The core engine is domain-agnostic; this folder only supplies `domain.yaml` + CSV + a short pitch.

> **Not clinical software.** Fully synthetic. Not ESI. Not for real triage.

## Run with the core CLI

```bash
cd /workspace/tabpfn-hack-core
tabpfn-hack demo \
  --domain examples/er-triage/domain.yaml \
  --data examples/er-triage/data/intake_encounters.csv \
  --mode mock
```

Seed CSV was copied from the old `/workspace/tabpfn-er-triage-scaffold/` tree. Expand with a generator if needed.

## Note

Prefer developing against the root generic pack (`domain.yaml` + `data/synthetic_table.csv`) unless judges want an ER story. Keep ER language out of the **core** README.
