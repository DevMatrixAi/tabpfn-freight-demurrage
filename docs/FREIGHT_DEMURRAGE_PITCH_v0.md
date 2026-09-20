# Freight demurrage triage desk — judge packet (v0)

**Entry face:** `tabpfn-hack-core` + pack `domains/freight-demurrage/` (Build to land)
**Audience:** Prior Labs judges · **Angle:** dwell fees on a spreadsheet, not model jargon
**Deadline:** 6 Oct 2026 23:59 CEST · **Judging:** 50% showcase / 30% creativity / 20% repro
**Status:** Soft-lock candidate per Gemini report + Build. Chargeback soft-lock is retired for the Spark path.

## Demo open (locked lead)

**$1.27M projected demurrage on the table** (`artifacts/freight-demurrage/demo_report.md`, mock run). First screen for judges and README. Then action counts: divert / rebook / expedite / authorize_fee / cancel_booking / monitor.

## One sentence

An ocean-freight exception desk that scores messy container tables for demurrage / detention risk and turns the tail of the dwell distribution into money moves: divert, rebook, expedite inland, authorize the fee, or cancel the booking.

## Pack facts (synced from `domain.yaml`)

| Field | Value |
| --- | --- |
| Label | `demurrage_risk` |
| Text | `terminal_note`, `weather_alert` |
| High-card | `bol_id`, `container_id`, `pol`, `pod` |
| Group / time | `vessel_id` / `event_ts` |
| Money cols | `free_days_left`, `daily_demurrage_usd`, `projected_demurrage_usd`, `cargo_value_usd` |
| Gates | `blank_sailing` → rebook · `inland_can_beat_freedays` → expedite · `fee_inevitable` → authorize_fee · `cargo_vs_fee_collapse` → cancel_booking |
| Data | 1200-row `data/containers.csv` |
| CLI | `tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --data domains/freight-demurrage/data/containers.csv` |

## Why a judge should care (P&L)

Containers that sit past free days burn cash as demurrage and detention. Fees can dwarf the box value. Ops already has vessel IDs, BOL numbers, terminal notes, missing milestones, and AIS-ish timing. They lack a fast dwell risk score plus a fixed playbook. This entry wires TabPFN-3.5 to that table and to MCP `suggest_actions` so an agent or human gets the next dollar action, not a ROC curve.

## Judge-face score (freight vs PA vs chargeback)

| Concept | 90s dollar clarity | Anti-wrapper (≥6/8) | Build / optics | Spark path |
| --- | --- | --- | --- | --- |
| **Freight demurrage** | High — fee column on screen | Thinking + text + high-card + missings + full dist → actions | Public AIS + synthetic; no PHI | **Preferred** |
| Healthcare PA (admin-only) | High — $ waste counter | Same surfaces + clinical text | Heavier synth; optics risk if language slips clinical | Dual-entry only if human wants |
| Chargeback desk | Medium — XGB can look fine | Weaker 50% delta | Already drafted | **No-go** for Spark |

## 50 / 30 / 20 map

| Weight | Criterion | Claim | Proof |
| --- | --- | --- | --- |
| **50% Showcase** | Real TabPFN-3.5 surface | Plus on terminal/weather notes; Thinking with `group_col=vessel_id` + time; Fast for triage; raw frames; high-card BOL/container IDs; missings; full predictive distribution for dwell days; baseline vs HistGBM/XGB that struggles on text + new IDs | `tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --mode thinking\|plus\|fast\|mock` |
| **30% Creativity** | Dollar actions | Playbook verbs below via `suggest_actions` + morning digest. Core stays pack-agnostic | MCP tools + pack README |
| **20% Repro** | Cold run | Apache-2.0; synthetic/public-derived CSV in-repo; mock path with no `TABPFN_TOKEN`; pytest offline | `pip install -e ".[dev]"` → demo → pytest |

## Action playbook (shipper language)

Scores use the dwell / demurrage risk distribution (demo: synthetic). Pair every action with the pack disclaimer.

| Action | When (draft gates) | Why it saves money |
| --- | --- | --- |
| **divert** | High upper-tail dwell at current terminal | Move box before free days burn |
| **rebook** | Blank sailing / schedule break + elevated risk | New vessel before penalty clock wins |
| **expedite** | Inland leg can still beat free-day cutoff | Pay truck/rail once, avoid daily fee spiral |
| **authorize_fee** | Fee already inevitable; lock budget from p90 exposure | Stop surprise invoices; pick the cheaper loss |
| **cancel_booking** | Cargo economics collapse vs projected demurrage | Cut the voyage before deeper loss |
| **monitor** | Else | Log score; leave in normal path |

## README first screen (dollar-first — frozen)

```text
# Freight demurrage triage (TabPFN-3.5)

Demo open: $1.27M projected demurrage on the table — then divert / rebook /
expedite / authorize_fee / cancel_booking before free days burn.

Synthetic / public-derived demo only. Not a carrier system of record.

pip install -e ".[dev]"
tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --data domains/freight-demurrage/data/containers.csv
```


## 90-second demo beat

1. **Open (0:00–0:15).** Spreadsheet of containers. Red line: projected demurrage $ on the free-day clock. No model talk yet.
2. **Run (0:15–0:40).** Mock/Thinking demo on freight pack. Point at text notes, BOL IDs, missing timestamps, `vessel_id` grouping.
3. **Showcase (0:40–1:05).** Baseline delta (GBDT weak on text/new IDs). Show predictive distribution / upper-tail dwell → fee math.
4. **Actions (1:05–1:25).** `suggest_actions`: divert / rebook / expedite / authorize_fee / cancel_booking.
5. **Repro (1:25–1:30).** “No token still runs mock. Apache-2.0. One command.”

## Anti-wrapper checklist (must hit ≥6 in one path)

1. Text cols (terminal / weather notes)
2. High-card (BOL, container, vessel)
3. Missings (milestones)
4. Thinking group/time (`vessel_id` + timestamp)
5. Fast vs Thinking/Plus routing (when backend ready)
6. Full predictive distribution → fee math
7. Baseline delta on screen
8. MCP `suggest_actions` with money verbs

## Non-goals (say out loud)

Synthetic / public-derived demo only. Not a TOS/Navis replacement, not customs advice, not production routing. Human owns Prior Labs register/submit and live token runs.

## Human still owns

Final concept lock, GitHub connect, Prior Labs join + `TABPFN_TOKEN`, submission form.
