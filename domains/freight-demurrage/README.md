# Freight demurrage triage (TabPFN-3.5)

Containers past free days burn demurrage. This desk scores messy vessel/BOL tables
(text notes, high-card IDs, missing milestones, vessel groups + time) with TabPFN-3.5
Plus / Thinking / Fast, shows the dwell distribution vs a GBDT baseline, then proposes
divert · rebook · expedite · authorize_fee via MCP.

Synthetic / public-derived demo only. Not a carrier system of record.

```bash
pip install -e ".[dev]"
tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --data domains/freight-demurrage/data/containers.csv
```
