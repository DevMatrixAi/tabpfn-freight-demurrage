# Chargeback / refund risk desk — judge one-pager (v0.1, pack-synced)

**Entry:** `tabpfn-hack-core` + `domains/chargeback-desk/`
**Audience:** Prior Labs judges · **Angle:** seller P&L, not model jargon
**Deadline:** 6 Oct 2026 23:59 CEST · **Judging:** 50% showcase / 30% creativity / 20% repro

## One sentence

A seller ops desk that scores messy order tables for chargeback / refund risk and turns the score into money moves: hold payout, cancel before ship, pause the ad buying bad traffic, confirm with the buyer, or pull evidence.

## Why a judge should care (P&L)

Chargebacks and friendly-fraud refunds hit margin twice: lost goods/fees and wasted ad spend on the same SKU or creative. Ops already has the table. They lack a fast score + a fixed playbook. This entry wires TabPFN-3.5 to that table and to MCP `suggest_actions` so an agent or human gets the next dollar action, not a ROC curve.

## Pack facts (synced from `domain.yaml`)

| Field | Value |
| --- | --- |
| Label | `chargeback_risk` |
| Text | `buyer_note`, `agent_note` |
| High-card | `customer_id`, `sku_id`, `campaign_id`, `device_id` |
| Group / time | `shop_id` / `order_ts` |
| Gates | `shipped=0` → cancel · `repeat_bad_source=1` → pause_ad |
| Data | 1200-row synthetic `data/orders.csv` |

## 50 / 30 / 20 map

| Weight | What judges look for | How this story proves it |
| --- | --- | --- |
| **50% Showcase** | Real TabPFN-3.5 surface | Plus / Thinking / Fast / local on raw orders: notes, high-card IDs, missings, `shop_id` + `order_ts` for Thinking; `predict_proba` as risk; baseline vs HistGBM/logistic |
| **30% Creativity** | Practical value | Chargeback desk playbook via `suggest_actions` (below). Core stays domain-agnostic |
| **20% Repro** | Cold run | Apache-2.0; synthetic CSV in-repo; mock demo + pytest with no `TABPFN_TOKEN` |

## Action playbook (seller language)

Order matches pack evaluation: hold → cancel → pause_ad → confirm → evidence → monitor.

| Action | Gate | Why it saves money |
| --- | --- | --- |
| **hold** | proba ≥ 0.80 | Stop payout/fulfillment into a likely loss |
| **cancel** | ≥ 0.68 and not shipped | Cut goods + fees before the box leaves |
| **pause_ad** | ≥ 0.45 and `repeat_bad_source` | Stop paying to acquire the next loss |
| **confirm** | ≥ 0.52 | Kill friendly fraud (address / intent) before release |
| **evidence** | ≥ 0.35 | Raise dispute win-rate (tracking, delivery, chat) |
| **monitor** | else | Normal path — log score only |

Demo disclaimer (loud): synthetic ecommerce chargeback demo only. Not a payments processor, fraud certification, or legal advice.

## 90-second demo beat

1. Show `orders.csv`: notes, customer/SKU/campaign IDs, shops, timestamps.
2. `tabpfn-hack demo --domain domains/chargeback-desk/domain.yaml` (mock) → report risk + baseline.
3. `suggest_actions` on top rows → hold / cancel / pause_ad / confirm / evidence.
4. “Token unlocks Plus/Thinking/Fast. No token still repros.”

## Human still owns

Final domain lock, GitHub connect, Prior Labs join + `TABPFN_TOKEN`, submission.
