# Concrete Constellation

An Obsidian-style graph view of India's construction-sector news sentiment.

**18,066 articles** (Aug 2024 to Aug 2026) from the PIF construction corpus,
clustered bottom-up into **12 thematic buckets** and scored with finBERT.
Every article is a single dust particle orbiting its cluster; the outer belt is
the 2,003 articles deliberately excluded from the index.

## The page

`index.html` is fully self-contained: no build step, no dependencies, no network
calls. All data is embedded. Open it directly or serve the folder statically.

- **Colour modes** : Health (finBERT net tone, diverging poles), Bucket (12
  categorical hues), Structure (neutral).
- **Time scrubber** : 25 monthly steps. Recolours only; the layout never moves,
  so the mental map survives. The scrubbed month's articles light up individually.
- **Controls** : filters (satellites, similarity edges, dust), display (node
  size, dust density, link width, label fade) and live force sliders.
- **Honesty** : months with fewer than 20 articles desaturate toward neutral,
  months with none render hollow, and the two crawl-date-inflated months plus the
  partial final month are flagged in the slider, legend and tooltips.

Below the graph: composite index, 12 small multiples on a shared scale, a
distress-vocabulary index, caveats and the full data table.

## Pipeline

Run in order from `pipeline/` against the corpus on the EILA drive:

| Step | Script | What it does |
|---|---|---|
| 1 | `discover_buckets.py` | MiniLM embeddings, UMAP, HDBSCAN, c-TF-IDF labels |
| 2 | `assign_buckets.py` | Collapse clusters into the 12 buckets; rescue HDBSCAN noise by nearest centroid |
| 3 | `bucket_sentiment.py` | finBERT tone per article, monthly aggregation, CSV export |

`construction_themes.py` holds the sector sub-themes and polarity signs;
`construction_sentiment.py` is the earlier hand-written-regex approach, kept for
reference and superseded by the discovered taxonomy.

Environment: Python 3.11, `torch==2.4.1`, `transformers==4.44.2`,
`sentence-transformers==2.7.0`. Newer transformers break against torch 2.4.

## Data

| File | Contents |
|---|---|
| `data/taxonomy.json` | The 12 buckets and the raw clusters each is built from |
| `data/REPORT.md` | All 52 discovered clusters with top terms and samples |
| `data/clusters.csv` | Article to HDBSCAN cluster assignment |
| `data/assignments.csv` | Article to final bucket, with method and similarity |
| `data/graph_data.json` | The payload embedded in the page |
| `data/bucket_sentiment_monthly.csv` | Monthly health per bucket |

## Method note

finBERT reads financial tone, not economic direction: "cement prices soar" scores
positive. Buckets here are topics rather than directional metrics, so tone is
reported as-is and the one trap (Input Costs) is flagged on the page. Equity
coverage was dropped from the index deliberately: share-price mood measures
investor sentiment, not whether anything is being built. Housing finance was
kept, since mortgage credit is real construction demand.

Pahlé India Foundation.

## 3D version

`3d.html` is a separate page (live at `/3d`) rendering the same data as a volume
in space: 3D force layout, perspective projection, a real starfield that
parallaxes, and every article as an individual mote on a spherical shell around
its cluster.

Build it with `python3 build3d.py` after editing `3d.src.html` — the source
carries a `__DATA__` placeholder and the build injects the payload from
`index.html`, so both pages always show the same numbers.

**Hand control** (that page only) uses MediaPipe Hands via jsdelivr and the
webcam. All inference is local; no frames leave the browser and nothing is
recorded. It is opt-in behind a button, runs at ~18fps, and stops when the tab
is hidden. Gestures: open palm orbits, pinch on a node picks it up, holding the
pinch drags it in 3D, two hands apart zoom, two pinches spreading expand the
picked cluster, a fist releases.

Performance: motes are batched by colour (one `fillStyle` per colour per frame
rather than 18,066), which keeps a full-density frame at roughly 6 ms.

## eShram constellation

`/eshram` (2D) and `/eshram-3d` render India's eShram registry of unorganised
workers with the same engines: 36 states as unsized anchors, 823 districts as
discs sized by state-calibrated registrations, 100 directed inter-state
corridors (82 with 2,000+ movers, 18 forced so no state is an orphan), 78
origin-state to destination-district corridors shown on hover, and 31,740 motes
where one mote is 10,000 registrations, each carrying its own gender and trade
group. The 2,445-dot belt is the gap between the data.gov.in dump (341.85M rows)
and the eShram dashboard's 317.4M distinct UANs.

Layout is geo-anchored by default (2024 LGD district boundaries, 781 of 823
matched; the rest sit at their state centroid) with a Map/Force slider that
blends toward the physics layout. Colour modes: Women (parity-pivoted female
share; motes coloured by their own gender), Work (LQ typology on discs, actual
trade on motes), Literacy (share not literate), Corridors (flow on edges,
neutral nodes). The scrubber runs over the seven trade groups, since the
registry has no time dimension.

Build: `python3 eshram/build_payload.py` (needs the EILA drive at
`/Volumes/EILA/PIF /eshram`, pandas, geopandas) then `python3 eshram/patch2d.py`
for the 2D page; the 3D page is `eshram-3d.src.html` with the payload injected.
Design spec and rejected alternatives: `eshram/SPEC.json`.
