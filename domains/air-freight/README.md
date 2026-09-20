# Air freight coda pack

Score messy AWB / station tables for **miss-connection / delay risk**, then suggest
**expedite AOG**, **hold for connection**, **rebook belly**, or **monitor**.

Multi-client (`client_id`) and multi-carrier (`carrier`) are **fixture columns only** —
demo slicing labels, not live airline APIs.

Coda pack on the demurrage spine. Same TabPFN engine.

```bash
tabpfn-hack demo --domain domains/air-freight/domain.yaml --mode mock
# or explicit:
tabpfn-hack demo --domain domains/air-freight/domain.yaml \
  --data domains/air-freight/data/shipments.csv --mode mock
```
