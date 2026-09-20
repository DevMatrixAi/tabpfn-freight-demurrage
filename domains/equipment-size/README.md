# Equipment size coda pack

Classify bookings that need **special equipment** (reefer / 40HC / hazmat-aware)
vs standard dry box — then suggest upsell 40HC, reefer hold, or confirm dry.

Coda pack on the demurrage spine. Same TabPFN engine; fixtures only.

```bash
tabpfn-hack demo --domain domains/equipment-size/domain.yaml
# or explicit:
tabpfn-hack demo --domain domains/equipment-size/domain.yaml \
  --data domains/equipment-size/data/bookings.csv --mode mock
```
