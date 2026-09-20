# Gemini Deep Research prompt — TabPFN-3.5 hackathon (DGX Spark) — v0.1 pitch edits

**Paste the block below into Gemini Deep Research.** Goal: find a product we can ship in ~2 weeks that wins Prior Labs TabPFN-3.5 Hackathon (deadline 6 Oct 2026 23:59 CEST) and is strong enough to found a company on.

---

## Research prompt (copy from here)

You are researching product opportunities for a Prior Labs **TabPFN-3.5 Hackathon** entry. First prize is an **NVIDIA DGX Spark**. We need a concept that (1) maximizes official judging, (2) is startup-foundable, (3) has enough proprietary process/IP that most competitors would hesitate to open-source it for a contest, and (4) can be built in ~14 days by a small team around TabPFN-3.5 + MCP.

### Official constraints (treat as hard)

- Event: Prior Labs TabPFN-3.5 Hackathon (platform.priorlabs.ai/hackathon-3.5).
- Judging weights: **50%** showcase of TabPFN-3.5 capabilities, **30%** creativity / practical value, **20%** technical quality + reproducibility.
- Must ship: public runnable repo, **Apache-2.0**, description a third party can follow; optional video.
- TabPFN-3.5 must be **core** (other tools OK). Multiple entries allowed; late submissions invalid.
- TabPFN-3.5 strengths to force in the demo: **text columns**, **high-cardinality categoricals**, **missing values**, **wide tables**, **Thinking** on grouped/temporal data (`group_col` / `group_time_col`), **Plus**, **Fast**, uncertainty via predictive probabilities, agentic **MCP** workflows.
- Do **not** propose a thin rewrap of Prior’s hosted MCP (`https://api.priorlabs.ai/mcp/server`). Winning entries add domain workflow: profiling, reports, action playbooks, baselines, digests.
- We already have a domain-agnostic engine (`tabpfn-hack-core`) with pluggable `domain.yaml` packs and a draft ecommerce chargeback desk pack — treat that as optional baseline, not sacred.

### What “blow away the field” means here

Rank opportunities by expected **judge score**, not by vibe:

1. **Showcase density (50%)**: How obviously does a 90-second demo prove 3.5-only wins vs XGBoost/HistGBM on messy real-world tables?
2. **Moat / IP hesitation (strategic)**: Would a serious startup hesitate to open-source this because it encodes proprietary playbooks, data contracts, evaluation harnesses, or vertical workflows? Prefer ideas where the *process + action layer* is the secret sauce while still satisfying Apache-2.0 for the submitted repo (clearly separate public demo vs future proprietary SaaS).
3. **Foundability**: Clear buyer, pain priced in dollars, wedge → platform, path to data network effects.
4. **Buildability in 14 days**: Synthetic or public data OK; no PHI/PD dependency; mock path without API key for repro.
5. **MCP agent story**: Natural language → load table → score → explain → **dollar actions** (not just predict).

### Domains to investigate (expand beyond chargebacks)

Search and compare at least **12 concrete product concepts** across:

- Fintech / payments risk / disputes / merchant ops
- Insurance intake & claims triage (synthetic-only demos)
- Healthcare **admin** ops (no clinical CDS; scheduling, eligibility, coding assist) — flag regulatory landmines
- Ecommerce / retail ops (refunds, chargebacks, inventory exceptions, ad waste)
- Logistics exception desks
- B2B SaaS churn + expansion desks
- Cyber / fraud ops queues (careful with dual-use)
- Climate / energy tabular ops
- Scientific / industrial sensor tables with text notes
- Government/benefits eligibility (synthetic)
- Marketplace trust & safety queues
- “Tabular agent OS” horizontal (risky for 50% unless demo is brutal)

For each concept provide:

- One-sentence pitch (buyer + dollar outcome)
- Why TabPFN-3.5 is uniquely required (map features → 3.5 capabilities)
- 5-action playbook example (like hold / confirm / cancel / evidence / pause-ad)
- Data reality: what columns look like; synthetic vs public datasets
- IP / open-source tension: what would stay proprietary post-contest
- Build risk in 14 days (H/M/L)
- Expected judge fit score 1–10 on 50/30/20 separately
- Top 3 competitors or substitutes (human teams, GBDT dashboards, LLM-only agents)


### Pitch / judge-narrative constraints (required)

Add these scoring axes so the report is usable by the pitch owner without a rewrite:

7. **90-second clarity**: Can a non-ML judge repeat the dollar story after one watch? Prefer concepts where the first screen is a spreadsheet of losses, not a model card.
8. **Action vocabulary**: Name 5 concrete money verbs (hold / cancel / pause-ad class). Reject concepts whose actions are only “flag” or “investigate.”
9. **Foundability vs contest conflict**: Flag ideas where publishing Apache-2.0 playbooks would actually kill the startup story — we need hesitation from *other* entrants, not self-sabotage. Prefer: public demo pack + thin playbook; proprietary depth post-contest.
10. **README first screen**: Draft the first 8 lines a judge reads (problem in $, TabPFN-3.5 proof points, one command to run). Score how hard that screen is to ignore.
11. **Anti-wrapper test**: List the exact TabPFN-3.5 surfaces the demo must show in 90s (text cols, high-card, missings, Thinking group/time, Plus/Fast, proba, baseline delta, MCP actions). Any concept that can’t hit ≥6 of these in one path is a no-go for the Spark prize.

Also rewrite failure mode #6 as a checklist judges would use to dismiss us.

### Specifically answer

1. What is the **single best** contest entry to maximize P(win DGX Spark)?
2. What is the **best startup** that still has a high contest win probability (may differ)?
3. Should we stick with **chargeback/refund risk desk**, pivot, or do a **dual entry** (core + two packs)?
4. How do we structure Apache-2.0 submission so the demo is fully reproducible while the long-term company retains playbook/IP leverage?
5. Killer 90-second demo script and README first screen that judges can’t ignore (dollar-first; no ML jargon in the first 20 seconds).
6. Failure modes: what would make judges say “nice wrapper” or “not really 3.5”?

### Output format

- Executive recommendation (half page)
- Ranked table of ≥12 concepts with scores
- Deep dive on top 3 (architecture, MCP tools, domain.yaml sketch, demo data plan)
- Explicit go / no-go on continuing the chargeback soft-lock
- Sources / links (Prior docs, TabArena/BeyondArena angles, vertical market reports)

Be concrete. No hype adjectives. Prefer products where losing the goods/fee/ad-dollar is obvious on a spreadsheet.

## End copy block

