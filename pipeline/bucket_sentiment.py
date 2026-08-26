"""finBERT sentiment per discovered bucket, monthly.

Scores every bucketed article's tone once (title + lead), then aggregates into a
monthly health series per bucket. health = BUCKET_SIGN x net_tone. All buckets
are activity/topic buckets where positive coverage = healthier sector, so signs
are +1; the one known finBERT trap (rising input costs read as 'positive') is
flagged in the report rather than silently flipped, because the costs bucket
mixes cost-inflation with asset-return stories.

  .venv/bin/python bucket_sentiment.py           # score + report
  .venv/bin/python bucket_sentiment.py --report   # aggregate only (after scoring)
"""
from __future__ import annotations
import argparse, csv, glob, json, os, sqlite3, time
import construction_themes as ct

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "bucket_discovery")
CORPUS = "/Volumes/EILA/PIF/construction-corpus"
SRC = CORPUS + "/india" if os.path.isdir(CORPUS + "/india") else CORPUS + "/articles"
DB = os.path.join(HERE, "bucket_sentiment.db")
TAX = json.load(open(f"{D}/taxonomy.json"))
NAME = {k: v["name"] for k, v in TAX.items() if not k.startswith("_")}
LEAD = 600
BATCH = 64
MODEL_VERSION = "ProsusAI/finbert@bucket1"

SCHEMA = """CREATE TABLE IF NOT EXISTS b_scores(
  id TEXT PRIMARY KEY, bucket TEXT, month TEXT, net REAL, label TEXT,
  distress INTEGER, model_version TEXT);"""


def load_text():
    """id -> title+lead, for the ids we bucketed."""
    want = {r["id"]: r for r in csv.DictReader(open(f"{D}/assignments.csv"))
            if r["bucket"] != "_drop"}
    txt = {}
    for path in glob.glob(SRC + "/*/*.json"):
        if "/._" in path:
            continue
        try:
            d = json.load(open(path))
        except Exception:
            continue
        if d["id"] in want and (d.get("body") or "").strip():
            txt[d["id"]] = f"{d.get('title') or ''}. {d['body'][:LEAD]}"
    return want, txt


def score():
    db = sqlite3.connect(DB); db.executescript(SCHEMA)
    done = {r[0] for r in db.execute("SELECT id FROM b_scores")}
    want, txt = load_text()
    todo = [i for i in want if i in txt and i not in done]
    print(f"[bucket] {len(want)} bucketed · text for {len(txt)} · to score {len(todo)}")
    if not todo:
        return db

    from transformers import pipeline
    import torch
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[finbert] {dev}")
    pipe = pipeline("text-classification", model="ProsusAI/finbert",
                    top_k=None, device=dev)
    t0 = time.time()
    for s in range(0, len(todo), BATCH):
        ids = todo[s:s + BATCH]
        texts = [txt[i] for i in ids]
        outs = pipe(texts, truncation=True, max_length=512, batch_size=BATCH)
        rows = []
        for i, probs in zip(ids, outs):
            p = {x["label"].lower(): float(x["score"]) for x in probs}
            net = round(p.get("positive", 0.) - p.get("negative", 0.), 4)
            label = max(p, key=p.get)
            r = want[i]
            rows.append((i, r["bucket"], r["month"], net, label,
                         int(ct.is_distress(txt[i])), MODEL_VERSION))
        db.executemany("INSERT OR REPLACE INTO b_scores VALUES (?,?,?,?,?,?,?)", rows)
        db.commit()
        if s and s % (BATCH * 20) == 0:
            print(f"[finbert] {s}/{len(todo)} · {s/(time.time()-t0):.0f}/s", flush=True)
    print(f"[finbert] scored {len(todo)} in {time.time()-t0:.0f}s")
    return db


def report(db=None):
    db = db or sqlite3.connect(DB)
    rows = db.execute("""SELECT bucket, month,
        SUM(label='positive'), SUM(label='negative'), COUNT(*)
        FROM b_scores WHERE month<>'' GROUP BY bucket, month""").fetchall()
    if not rows:
        print("no scores yet"); return
    from collections import defaultdict
    series = defaultdict(dict)     # bucket -> month -> (health, n)
    for b, m, pos, neg, n in rows:
        series[b][m] = ((pos - neg) / n, n)
    months = sorted({m for b in series.values() for m in b})
    recent = months[-13:]

    order = sorted(NAME, key=lambda b: -sum(v[1] for v in series[b].values()))
    print(f"\nBUCKET HEALTH  (net tone -1..+1, by month)   months {recent[0]}..{recent[-1]}")
    hdr = "bucket".ljust(30) + "".join(f"{m[2:]:>7}" for m in recent) + f"{'n':>8}"
    print(hdr)
    for b in order:
        tot = sum(v[1] for v in series[b].values())
        line = NAME[b][:29].ljust(30)
        for m in recent:
            line += (f"{series[b][m][0]:>7.2f}" if m in series[b] else f"{'·':>7}")
        print(line + f"{tot:>8}")

    # composite: n-weighted mean health across buckets, per month
    print("\nSECTOR COMPOSITE  (article-weighted mean, all buckets)")
    comp = []
    for m in months:
        num = sum(series[b][m][0]*series[b][m][1] for b in series if m in series[b])
        den = sum(series[b][m][1] for b in series if m in series[b])
        if den: comp.append((m, num/den, den))
    print("  " + "  ".join(f"{m[2:]}:{h:+.2f}" for m, h, _ in comp[-13:]))

    d = db.execute("""SELECT month, AVG(distress) FROM b_scores
        WHERE month<>'' GROUP BY month ORDER BY month""").fetchall()
    print("\nDISTRESS SHARE  (slowdown/stalled/insolvency vocab)")
    print("  " + "  ".join(f"{m[2:]}:{v*100:.0f}%" for m, v in d[-13:]))

    # CSV to EILA for the dashboard / decks
    out = f"{CORPUS}/exports/bucket_sentiment_monthly.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["bucket_id","bucket","month","health","n"])
        for b in order:
            for m in sorted(series[b]):
                h, n = series[b][m]
                w.writerow([b, NAME[b], m, round(h,4), n])
    print(f"\n[csv] {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    report() if a.report else report(score())
