# India Construction Sentiment Index — Master Context

**Purpose of this file.** A cold-start briefing for an AI assistant helping someone
brainstorm on this project. It carries the state, the decisions already taken (and
why), the traps, and the open questions. Read it end to end before proposing
anything — several obvious-looking ideas here have already been tried and rejected
for reasons that are not obvious.

Last verified: **26 August 2026**. Owner: Aryan Singh, Pahlé India Foundation (PIF),
an economics policy think tank in India.

---

## 1. What this project is

Build a **sentiment index for India's construction sector** from news coverage —
a monthly indicator that says whether the discourse around Indian construction is
improving or deteriorating, broken into themes, defensible enough for a think tank
to publish.

Three layers, deliberately separated:

| Layer | What it does | Status |
|---|---|---|
| **Corpus** | Every India construction article, 24 months, full text | Live, still collecting |
| **Model** | Scores each article's sentiment | finBERT today; own model planned |
| **Index** | Buckets → weights → one number | Buckets done; rubric decided, not implemented |

A public visualisation already exists at **https://concrete-constellation.vercel.app**.

---

## 2. Current state

### Corpus (collecting, unattended)
- Location: `/Volumes/EILA/PIF/construction-corpus/` on an external drive named EILA.
  **If the drive is unmounted, most of this project is unreachable.**
- **36,637 records discovered, 23,712 with full body text.** Still growing — five
  `launchd` jobs (`org.pif.construction-corpus`, `-paid`, `-gnews`, `-watchdog`,
  `-caffeinate`) run continuously. Currently pass 3, slot 9 of 77.
- India-filtered subset: **20,108 articles** in `india/<YYYY-MM>/<id>.json`.
- Collectors: Wayback CDX (14.6k), publisher sitemaps (11.7k), Google News RSS (4.4k),
  GDELT (3.1k), a seed list from an earlier pipeline (1.5k), ET archive via paid
  login (1.1k).
- Exports in `exports/`: a 6 MB CSV, a 76 MB self-contained HTML reader, a 42 MB zip.

### Scoring (done, on the old model)
- **18,066 articles scored** with finBERT (`ProsusAI/finbert`), Aug 2024 – Aug 2026.
- SQLite at `~/pif-econ-sentiment/worker/bucket_sentiment.db`.

### Buckets (done)
Discovered bottom-up, not hand-written: MiniLM embeddings → UMAP → HDBSCAN → c-TF-IDF
labels → 52 raw clusters → manually collapsed to **12 buckets**.

| Bucket | n |
|---|---|
| Residential Real Estate | 4,242 |
| Policy, Regulation & Schemes | 2,048 |
| Cement | 1,607 |
| Railways & Metro | 1,562 |
| Roads & Highways | 1,291 |
| Site Safety, Accidents & Legal | 1,211 |
| Housing Finance / Credit | 1,210 |
| Commercial RE & Data Centres | 1,205 |
| EPC / Orders / Contracts | 1,187 |
| Construction Industry (macro) | 989 |
| Airports & Ports | 982 |
| Input Costs & Macro Shocks | 532 |

**2,003 articles were deliberately excluded**: 601 junk clusters (brand/PR copy,
paywall stubs, listing pages) and 1,402 equity-market articles. See §5 for why the
equity cut matters.

### Website (live)
- **https://concrete-constellation.vercel.app** — Vercel project
  `concrete-constellation`, account `aryansingh-8099`. Static, no build step.
- Repo: **https://github.com/themonkkey/concrete-constellation** (public, `main`).
  Note the machine's `gh` CLI is authenticated as a *different* account
  (`aryaninternships-netizen`), so `gh` commands do not target this repo by default.
- Auto-deploy on push is **not** wired (the Vercel account lacks GitHub App access to
  `themonkkey`). Redeploy manually: `cd ~/concrete-constellation && vercel deploy --prod --yes`.

---

## 3. Where things live

| Path | What |
|---|---|
| `~/concrete-constellation/` | The published site + pipeline copies + this file |
| `~/pif-econ-sentiment/worker/` | **All working code lives here**, including corpus collectors |
| `/Volumes/EILA/PIF/construction-corpus/` | The corpus itself |
| `~/pif-econ-sentiment/worker/.venv` | Python 3.11 venv with torch |

Confusingly, the code sits inside a repo named `pif-econ-sentiment` — that was an
earlier, separate project (a macro-economy sentiment index) whose worker directory
this project grew inside. They share a venv and some modules.

Key scripts, in run order:

1. `discover_buckets.py` — embed, UMAP, HDBSCAN, c-TF-IDF. Caches embeddings so
   re-clustering with different parameters is cheap (`--recluster`).
2. `assign_buckets.py` — collapse clusters into the 12 buckets; rescue HDBSCAN noise
   by nearest centroid.
3. `bucket_sentiment.py` — finBERT tone per article, monthly aggregation, CSV export.
4. `construction_themes.py` — sub-themes and polarity signs (being retired, see §5).
5. `corpus_supervisor.py`, `paid_fetch.py`, `sitemap_crawl.py` — the collectors.

**Environment pins that matter:** `torch==2.4.1`, `transformers==4.44.2`,
`tokenizers==0.19.1`, `sentence-transformers==2.7.0`. Installing a newer
sentence-transformers pulls transformers 5.x, which **NameErrors against torch 2.4.1**
on import. If imports suddenly break, this is why. Machine is an **M2, 16 GB** — MPS
works, CUDA does not exist here.

---

## 4. Decisions already taken (do not re-litigate without new information)

**Buckets are discovered, not designed.** An earlier version used hand-written regex
themes. It was replaced because hand-written themes impose a taxonomy rather than
finding one. The regex version still exists (`construction_sentiment.py`) but is
superseded.

**12 buckets nest into 4 pillars** for weighting purposes:
- *Demand & Activity* — Residential RE, Commercial RE & Data Centres, EPC/Orders, Construction (macro)
- *Public Infrastructure* — Roads & Highways, Railways & Metro, Airports & Ports
- *Costs & Finance* — Cement, Input Costs, Housing Finance/Credit
- *Governance & Risk* — Policy & Regulation, Site Safety & Legal

Reason: weighting 12 things silently converts *where the clustering happened to cut*
into an economic judgement. Real estate split into two clusters and public
infrastructure into three; flat equal weighting would assert that housing matters
16.7% and public infra 25%, which nobody decided.

**The rubric (decided, not yet implemented):**
1. **z-score each bucket** over the full window before aggregating. Non-negotiable:
   bucket volatility ranges 0.082 to 0.299 (a 3.6× spread), so without this the
   loudest buckets drive the index regardless of the weights.
2. Four pillars, equal weight within pillar.
3. Pillar weights by **budget allocation** with a PIF panel, opened on an economic
   anchor (construction GVA and capex shares from MoSPI National Accounts, Union
   Budget expenditure profile, MoSPI Supply Use Tables, RBI sectoral credit).
4. Linear (compensatory) aggregation.
5. Publish a **sensitivity band** — the index under equal, volume, and chosen weights.

Rejected, with reasons: **PCA/factor** (22 clean months against 12 buckets overfits,
and weights shift every time a month is added, breaking back-series comparability);
**entropy** (would hand Input Costs 3.6× Site Safety on volatility alone);
**benefit-of-the-doubt/DEA** (makes every month look as good as possible);
**regression on an external target** (right idea, revisit at ~40 months, at pillar
level, regularised).

Useful empirical result: **volume-weighted and equal-weighted composites correlate
0.867** across the 22 clean months. The weighting choice moves the index at the
margin without flipping the story — so it can be chosen on principle, and that
correlation is worth publishing as robustness evidence.

**Output framing: a diffusion index, PMI-style, 50 = neutral.** Once labels mean
direction rather than tone, this is the natural form and PIF's audience already knows
how to read it.

---

## 5. Traps — the expensive lessons

**finBERT scores financial tone, not economic direction.** It reads "cement prices
soar" as POSITIVE because *soar* is bullish in market language. But rising input
costs are bad for construction. This was patched with a `THEME_SIGN` table that flips
the sign on cost-like themes. The patch is a workaround, not a fix — see §6.

**Equity coverage was cut on purpose.** 1,402 articles about realty stock prices,
Nifty Realty, IPOs and quarterly results were removed from the index. Share-price
movement measures *investor mood*, not whether anything is being built. Housing
finance was **kept** (1,210 articles) because mortgage credit is real construction
demand. If someone proposes "add the stock coverage back for more data", this is why
not.

**Volume weighting imports collection bias.** Residential Real Estate is 23.5% of
articles partly because Moneycontrol and ET Realty publish a lot of property copy and
the sitemap crawl hit them hardest. That is a media-market artefact, not an economic
weight.

**Two months have inflated counts: 2024-08 and 2026-02.** Wayback rows carry the
*crawl* timestamp, not the publish date, so archived batches pile onto the month they
were archived. **2026-08 is a partial month** (163 articles). All three are flagged
on the site; exclude them from any statistic that assumes even coverage.

**Cluster-months are thin.** Median n = 8 per cluster-month, 83% below 20. Bucket-months
are fine (median 47). Any per-cluster time series needs shrinkage toward the parent
bucket, not a hard cutoff that would blank most of the data.

**Corpus collection gotchas** (all cost real debugging time):
- Wayback `id_/` replays return original gzip bytes with no Content-Encoding header —
  must sniff magic bytes or every article parses as binary garbage.
- archive.org does not send 429 when angry; it refuses TCP connections (Errno 61), and
  retrying extends the ban. There is a 30-minute circuit breaker for this.
- Two collector loops must never share a state file — each loads the whole dict and
  writes it back, so the slower writer erases the other's work.
- Playwright must launch real Chrome (`channel="chrome"`), not bundled Chromium, or it
  cannot see the logged-in profile.

---

## 6. The live question: building a domain model

The decision has been taken to **replace finBERT with a construction-specific model**,
provisionally "IndiaConstructionBERT". Nothing has been built yet. This is where
brainstorming help is most useful.

**The critical insight, which is easy to get wrong:** the "cement prices soar" problem
is **not** fixed by domain pretraining. Masked-language pretraining teaches the model
what construction text *looks like*, not what is good for the sector. That fix lives
entirely in the **labelled fine-tuning data**. One could skip pretraining entirely,
fine-tune on a few thousand well-labelled articles, and capture most of the gain. The
labelled dataset is the project; pretraining is a multiplier on it.

**The label schema hinges on one sentence**, which resolves every ambiguous case:

> *Does this make construction activity in India more likely, cheaper, or faster?*
> Score from the perspective of building getting done, not any single firm's share price.

Labels: `expansion` / `contraction` / `neutral-factual`, plus **intensity** (marginal
or material) and **aspect** (which bucket the sentiment attaches to — this gives
aspect-based sentiment for free and lets one article count honestly in two buckets).

**Pretraining reality check.** The corpus is ~22M tokens / 87 MB. The
domain-adaptive-pretraining literature uses 1–10 GB, so this is 1–2% of typical scale.
Expect modest gains and watch for catastrophic forgetting: low learning rate, 2–4
epochs, hold out a slice for perplexity, and judge on downstream F1 rather than MLM
loss. The pool can be enlarged with policy text (PIB releases, RBI bulletins, MoSPI
and NSO reports, Budget documents, CREDAI/NAREDCO/CII reports, NHAI and Railways
annual reports) — plausibly another 50–150 MB in exactly the right register.

**Base checkpoint is open.** Candidates considered: `bert-base-uncased` (clean lineage
for the "ConstructionBERT" name, but 2018 architecture and a 512-token window),
`ProsusAI/finbert` (already financially adapted, but carries the tone bias being
escaped), `deberta-v3-base` (stronger classifier), `answerdotai/ModernBERT-base`
(recommended — 8k context). **Context length is the quiet argument**: articles average
3,503 characters, so a 512-token window has been reading only the lead and discarding
most of the body this entire time.

Extend the tokenizer either way — WordPiece shreds NHAI, RERA, mtpa, crore, lakh, EPC,
FSI, TDR, BHK, IBC, Bharatmala. Add 200–500 domain tokens and resize embeddings
*before* pretraining.

**Gates that should not be skipped:**
1. Two annotators label the same 100 articles first. Below Cohen's κ 0.7, rewrite the
   guideline — labelling 10,000 more only scales the confusion.
2. Gold test set of 600–800 human-labelled articles, stratified across all 12 buckets
   and 24 months. Never LLM-touched, never trained on, never used for hyperparameters.
3. Judge pretraining on downstream F1; drop it if the no-pretraining baseline matches.
4. Beat three baselines: finBERT as-is, finBERT with the current sign flips, and the
   base model without pretraining.
5. **Validate outward** — correlate the monthly index against IIP-construction, cement
   production, steel consumption, NHAI awards. This is both the credibility chart and
   the honest test of whether any of it beat finBERT.

Bulk labelling is expected to be LLM-assisted with rationales, with a 10% human audit
and an active-learning loop (score the unlabelled pool, label what the model is least
confident about, retrain).

---

## 7. The visualisation

`index.html` is one self-contained file — all data embedded, no dependencies, no
network calls, no build step. It renders an Obsidian-style force graph on canvas:

- 12 bucket hubs and 44 cluster satellites, physics hand-rolled (velocity Verlet,
  repulsion, springs, centring).
- **Every one of the 18,066 articles is a dust particle** orbiting its cluster,
  coloured by its own score. The 2,003 excluded articles form an outer belt.
- Three colour modes (health / bucket / structure), a 25-month scrubber that
  **recolours without ever re-laying-out**, and a control panel (filters, display,
  force sliders).
- Below the graph: composite line, 12 small multiples on a shared scale, a distress
  index, caveats and the data table.

Rendering lessons worth knowing before touching it:
- `var()` is inert inside SVG presentation attributes *and* canvas fill styles — read
  tokens via `getComputedStyle` or use literals.
- Physics must repel by the **visible footprint** (core + dust spread), not the core
  radius, or coronas interpenetrate and labels collide.
- rAF timestamps can lag `performance.now()`; seed tween start from the first frame and
  clamp progress to [0,1], or colours extrapolate into garbage.
- Under headless Chrome `--virtual-time-budget`, CSS transitions do not advance, so
  `getComputedStyle().opacity` lies. Trust screenshots.

Two reusable skills were written from this work and live at `~/.claude/skills/`:
`obsidian-graph` (look and behaviour) and `graph-encoding` (what channels should mean).

---

## 8. Open questions worth brainstorming

1. **Pillar weights.** What reference year and what exact GVA/capex split? Who sits on
   the panel? How are the adjustments recorded so provenance survives review?
2. **Base checkpoint.** Is the "ConstructionBERT" branding worth taking a 2018
   architecture and a 512-token window, or does ModernBERT's 8k context win?
3. **Is DAPT worth it at all** at 22M tokens, or should effort go entirely into labels
   and corpus expansion?
4. **Intensity and aspect** — worth the extra annotation cost, or does a clean
   three-way label get 90% of the value?
5. **Publication cadence and form.** Monthly note? Live dashboard? Both? What is the
   revision policy when late-arriving articles change a past month?
6. **Corpus coverage of the older half.** Recent months are denser than 2024–25. Does
   the index need a coverage correction, or is z-scoring per bucket enough?
7. **Sub-national cut.** The corpus has city and state signal (NCR, Mumbai, Bengaluru,
   Hyderabad). Is a state-level or metro-level index viable, or too thin?

---

## 9. Related projects (context only)

- **`pif-econ-sentiment`** — the parent project, a macro-economy sentiment index over 6
  themes (growth, inflation, jobs, markets, trade, fiscal), same finBERT approach. Its
  dashboard is at pif-econ-sentiment.vercel.app but **its Supabase instance is dead**
  (free tier paused it; DNS returns NXDOMAIN), so the page loads and shows no data.
  This construction project uses local SQLite and does not touch Supabase.
- The `THEME_SIGN` sign-flip trick and the "R-word" distress-vocabulary index both came
  from that project.

---

## 10. Working notes for whoever picks this up

- The corpus is **still growing**, so any count in this file is a floor, not a fixed
  number. Re-run `assign_buckets.py` and `bucket_sentiment.py` to pick up new articles;
  both are idempotent and skip what is already scored.
- Nothing in the pipeline needs a GPU. Everything here has run on an M2 laptop.
- No credentials are recorded in this file by design. If a step needs auth (the paid
  publisher logins, GitHub, Vercel), the human runs it.
- The honest summary of where this stands: **the corpus is real and good, the buckets
  are defensible, the index framing is decided, and the model is the next real piece of
  work.** The current finBERT numbers are a working baseline, not a publishable result
  — they measure financial tone with a sign patch, which is exactly the thing the new
  model is meant to replace.

---

## 11. Addendum (4 Sep 2026): the eShram constellation

The same repo now also hosts an unrelated dataset rendered with the same engines:
India's eShram registry of unorganised workers (341.85M dump rows; 317.4M distinct
UANs on the official dashboard), at `/eshram` and `/eshram-3d`. It is a structure
map, not a sentiment index: states are anchors, districts are discs, corridors are
inter-state registrations, and every mote is 10,000 people. Design spec and the
rejected alternatives are in `eshram/SPEC.json`; the builder is
`eshram/build_payload.py`. It shares nothing with the construction index except
the rendering code, and its data lives at `/Volumes/EILA/PIF /eshram/agg`.
