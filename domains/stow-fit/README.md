# Stow-fit coda pack

Recommend **equipment / mode** from cargo dims, weight, hazmat, temp, and value
(`dry20`, `dry40`, `hc40`, `reefer`, `air_belly`, `ltl_truck`), then suggest
**reefer hold**, **upsell 40HC**, **split load**, **air expedite**, **book LTL**,
or **monitor**.

**Honest:** tabular suggestion head only — **not** a 3D bin packer or WMS.

Multi-client (`client_id`) and multi-carrier (`carrier`) are fixture columns.
Coda pack on the demurrage spine. Same TabPFN engine.

```bash
tabpfn-hack demo --domain domains/stow-fit/domain.yaml --mode mock
# or explicit:
tabpfn-hack demo --domain domains/stow-fit/domain.yaml \
  --data domains/stow-fit/data/shipments.csv --mode mock
```
