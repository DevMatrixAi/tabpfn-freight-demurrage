# Inland mode coda pack

Score **truck vs rail** inland moves (and when to expedite) from messy
terminal / lane tables — distance, free days, cost gap, appointment tightness.

Coda pack on the demurrage spine. Same TabPFN engine; fixtures only.

```bash
tabpfn-hack demo --domain domains/inland-mode/domain.yaml
# or explicit:
tabpfn-hack demo --domain domains/inland-mode/domain.yaml \
  --data domains/inland-mode/data/moves.csv --mode mock
```
