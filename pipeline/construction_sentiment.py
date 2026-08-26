"""Sentiment index for the India construction corpus.

Reads the India-filtered corpus on EILA (india/<YYYY-MM>/<id>.json), tags each
article into construction sub-themes, scores tone with finBERT, and stores the
result in a local SQLite file. Supabase is not used here: the econ-sentiment
project is on the free tier and the instance is currently paused.

Idempotent — an article already scored with the same model version is skipped,
so this can run against a corpus the collectors are still growing.

  .venv/bin/python construction_sentiment.py                # score everything new
  .venv/bin/python construction_sentiment.py --limit 200    # smoke test
  .venv/bin/python construction_sentiment.py --report       # aggregate only
  .venv/bin/python construction_sentiment.py --report --csv out.csv
"""
from __future__ import annotations
import argparse, glob, json, os, sqlite3, sys, time

import construction_themes as ct

CORPUS = "/Volumes/EILA/PIF/construction-corpus"
SRC = CORPUS + "/india" if os.path.isdir(CORPUS + "/india") else CORPUS + "/articles"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "construction_sentiment.db")
MODEL_VERSION = "ProsusAI/finbert@1"
MIN_CHARS = 300          # below this the body is a stub, not an article
TEXT_CHARS = 1200        # finBERT sees 512 tokens; the lead carries the tone
BATCH = 32

SCHEMA = """
CREATE TABLE IF NOT EXISTS c_articles (
  id TEXT PRIMARY KEY, title TEXT, url TEXT, source TEXT, domain TEXT,
  published_at TEXT, month TEXT, n_chars INTEGER, is_distress INTEGER);
CREATE TABLE IF NOT EXISTS c_scores (
  article_id TEXT, theme TEXT, label TEXT, net REAL, model_version TEXT,
  scored_at TEXT, PRIMARY KEY (article_id, theme));
CREATE INDEX IF NOT EXISTS ix_c_articles_month ON c_articles(month);
"""


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB)
    db.executescript(SCHEMA)
    return db


def iter_articles():
    """Yield usable article dicts from the corpus, newest month last."""
    for path in sorted(glob.glob(SRC + "/*/*.json")):
        if "/._" in path:                      # macOS AppleDouble sidecars
            continue
        try:
            d = json.load(open(path))
        except Exception:
            continue
        if d.get("fetch_status") != "ok":
            continue
        body = (d.get("body") or "").strip()
        if len(body) < MIN_CHARS:
            continue
        d["body"] = body
        yield d


def month_of(d: dict) -> str:
    return (d.get("published_at") or "")[:7]


def score_all(limit: int | None, stub: bool) -> None:
    db = connect()
    done = {r[0] for r in db.execute(
        "SELECT article_id FROM c_scores WHERE model_version=? AND theme='overall'",
        (MODEL_VERSION,))}
    print(f"[corpus] {SRC}  ·  already scored: {len(done)}")

    if stub:
        from score import StubScorer
        scorer, batch_score = StubScorer(), None
    else:
        from transformers import pipeline
        import torch
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"[model] finBERT on {device}")
        pipe = pipeline("text-classification", model="ProsusAI/finbert",
                        top_k=None, device=device)
        def batch_score(texts):
            out = pipe(texts, truncation=True, max_length=512, batch_size=BATCH)
            res = []
            for probs in out:
                p = {x["label"].lower(): float(x["score"]) for x in probs}
                res.append({"label": max(p, key=p.get),
                            "net": round(p.get("positive", 0.) - p.get("negative", 0.), 4)})
            return res

    pending, seen, t0 = [], 0, time.time()

    def flush():
        nonlocal pending
        if not pending:
            return
        texts = [p[1] for p in pending]
        scores = batch_score(texts) if batch_score else [scorer.score(t) for t in texts]
        rows_a, rows_s = [], []
        for (d, text), s in zip(pending, scores):
            rows_a.append((d["id"], d.get("title"), d.get("url"), d.get("source"),
                           d.get("domain"), d.get("published_at"), month_of(d),
                           int(d.get("n_chars") or len(d["body"])),
                           int(ct.is_distress(text))))
            for theme in ct.tag(text):
                rows_s.append((d["id"], theme, s["label"], s["net"],
                               MODEL_VERSION, time.strftime("%Y-%m-%dT%H:%M:%S")))
        db.executemany("INSERT OR REPLACE INTO c_articles VALUES (?,?,?,?,?,?,?,?,?)", rows_a)
        db.executemany("INSERT OR REPLACE INTO c_scores VALUES (?,?,?,?,?,?)", rows_s)
        db.commit()
        pending = []

    for d in iter_articles():
        if d["id"] in done:
            continue
        pending.append((d, f"{d.get('title') or ''}. {d['body'][:TEXT_CHARS]}"))
        seen += 1
        if len(pending) >= BATCH:
            flush()
            if seen % (BATCH * 10) == 0:
                rate = seen / max(time.time() - t0, 1e-6)
                print(f"[score] {seen} new · {rate:.1f}/s", flush=True)
        if limit and seen >= limit:
            break
    flush()
    n = db.execute("SELECT COUNT(*) FROM c_articles").fetchone()[0]
    print(f"[done] +{seen} scored in {time.time()-t0:.0f}s · corpus total {n}")


def report(csv_path: str | None) -> None:
    db = connect()
    rows = db.execute("""
        SELECT a.month, s.theme,
               SUM(s.label='positive'), SUM(s.label='negative'), COUNT(*)
        FROM c_scores s JOIN c_articles a ON a.id = s.article_id
        WHERE s.model_version = ? AND a.month <> ''
        GROUP BY a.month, s.theme ORDER BY a.month, s.theme""",
        (MODEL_VERSION,)).fetchall()
    if not rows:
        print("no scores yet — run without --report first")
        return
    out = []
    for month, theme, pos, neg, n in rows:
        tone = (pos - neg) / n
        out.append({"month": month, "theme": theme, "n": n,
                    "tone": round(tone, 4),
                    "health": round(ct.THEME_SIGN.get(theme, 1) * tone, 4)})

    months = sorted({r["month"] for r in out})
    themes = ["overall"] + [t for t in ct.THEMES]
    print(f"\nHEALTH  (sign-adjusted net tone, -1..+1)   months={len(months)}")
    print("month    " + "".join(f"{t[:8]:>9}" for t in themes))
    for m in months:
        by = {r["theme"]: r for r in out if r["month"] == m}
        line = f"{m}  " + "".join(
            (f"{by[t]['health']:>9.3f}" if t in by else f"{'·':>9}") for t in themes)
        print(line + f"   n={by.get('overall', {}).get('n', 0)}")

    d = db.execute("""SELECT month, AVG(is_distress) FROM c_articles
                      WHERE month <> '' GROUP BY month ORDER BY month""").fetchall()
    print("\nDISTRESS SHARE (slowdown/stalled/insolvency vocabulary)")
    print("  " + "  ".join(f"{m}:{v*100:.0f}%" for m, v in d[-12:]))

    if csv_path:
        import csv as _csv
        with open(csv_path, "w", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=["month", "theme", "n", "tone", "health"])
            w.writeheader(); w.writerows(out)
        print(f"\n[csv] {csv_path}  ({len(out)} rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--stub", action="store_true", help="keyword scorer, no torch")
    ap.add_argument("--report", action="store_true", help="aggregate only")
    ap.add_argument("--csv")
    a = ap.parse_args()
    if a.report:
        report(a.csv)
    else:
        score_all(a.limit, a.stub)
        report(a.csv)
