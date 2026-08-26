"""Discover thematic buckets in the India construction corpus, bottom-up.

Pipeline (BERTopic recipe, run by hand so we keep control):
  1. text  = title + lead (first LEAD_CHARS of body)
  2. embed  = all-MiniLM-L6-v2, local, MPS, cached to embeddings.npy
  3. reduce = UMAP -> 5 dims (cosine)
  4. cluster= HDBSCAN (finds k, marks noise as -1)
  5. label  = c-TF-IDF top terms per cluster + 3 sample titles

Nothing here writes to the corpus. Outputs land in ./bucket_discovery/:
  embeddings.npy  meta.parquet-less (meta.json)  clusters.csv  REPORT.md

Re-run is cheap: embeddings are cached, so re-clustering with different
--min-cluster-size only redoes UMAP+HDBSCAN (seconds).

  .venv/bin/python discover_buckets.py                     # full run
  .venv/bin/python discover_buckets.py --min-cluster-size 80
  .venv/bin/python discover_buckets.py --recluster         # reuse cached embeddings
"""
from __future__ import annotations
import argparse, glob, json, os, re, time
import numpy as np

CORPUS = "/Volumes/EILA/PIF/construction-corpus"
SRC = CORPUS + "/india" if os.path.isdir(CORPUS + "/india") else CORPUS + "/articles"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bucket_discovery")
os.makedirs(OUT, exist_ok=True)
EMB = os.path.join(OUT, "embeddings.npy")
META = os.path.join(OUT, "meta.json")
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LEAD_CHARS = 400
MIN_CHARS = 300

# ultra-generic tokens that would otherwise dominate every cluster label
STOP_EXTRA = {"said","also","per","cent","year","years","rs","crore","lakh","lakhs",
    "company","companies","ltd","limited","india","indian","new","told","would",
    "will","also","month","months","time","first","last","week","day","cr","mn",
    "bn","reuters","pti","ians","read","full","news","com"}


def load_corpus():
    texts, meta = [], []
    for path in sorted(glob.glob(SRC + "/*/*.json")):
        if "/._" in path:
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
        title = (d.get("title") or "").strip()
        texts.append(f"{title}. {body[:LEAD_CHARS]}")
        meta.append({"id": d["id"], "title": title, "source": d.get("source"),
                     "month": (d.get("published_at") or "")[:7], "url": d.get("url")})
    return texts, meta


def embed(texts):
    import torch
    from sentence_transformers import SentenceTransformer
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[embed] {len(texts)} docs on {dev}")
    m = SentenceTransformer(MODEL, device=dev)
    t0 = time.time()
    v = m.encode(texts, batch_size=128, normalize_embeddings=True,
                 show_progress_bar=True)
    print(f"[embed] done in {time.time()-t0:.0f}s -> {v.shape}")
    return np.asarray(v, dtype=np.float32)


def c_tf_idf(labels, texts, topn=12):
    """Class-based TF-IDF (BERTopic): terms that mark each cluster vs the rest."""
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.feature_extraction import text as sktext
    stop = set(sktext.ENGLISH_STOP_WORDS) | STOP_EXTRA
    ids = sorted(set(labels) - {-1})
    joined = [" ".join(t for t, l in zip(texts, labels) if l == cid) for cid in ids]
    cv = CountVectorizer(stop_words=list(stop), ngram_range=(1, 2),
                         min_df=8, max_features=40000, token_pattern=r"[A-Za-z][A-Za-z-]{2,}")
    X = cv.fit_transform(joined).toarray().astype(float)   # clusters x terms
    words = np.array(cv.get_feature_names_out())
    tf = X / np.maximum(X.sum(axis=1, keepdims=True), 1)
    total = X.sum(axis=0)
    A = X.sum() / X.shape[0]
    idf = np.log(1 + A / np.maximum(total, 1))
    score = tf * idf
    out = {}
    for i, cid in enumerate(ids):
        top = words[np.argsort(score[i])[::-1][:topn]]
        out[cid] = list(top)
    return out


def main(a):
    if a.recluster and os.path.exists(EMB):
        v = np.load(EMB)
        meta = json.load(open(META))
        texts = [m["title"] + ". " for m in meta]   # titles enough for labeling
        print(f"[cache] reusing {v.shape} embeddings")
    else:
        texts, meta = load_corpus()
        v = embed(texts)
        np.save(EMB, v)
        json.dump(meta, open(META, "w"))

    import umap, hdbscan
    print(f"[umap] {v.shape} -> 5d")
    t0 = time.time()
    red = umap.UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                    metric="cosine", random_state=42).fit_transform(v)
    print(f"[umap] {time.time()-t0:.0f}s")

    print(f"[hdbscan] min_cluster_size={a.min_cluster_size}")
    cl = hdbscan.HDBSCAN(min_cluster_size=a.min_cluster_size, min_samples=10,
                         metric="euclidean", cluster_selection_method="eom")
    labels = cl.fit_predict(red)
    n_clusters = len(set(labels) - {-1})
    n_noise = int((labels == -1).sum())
    print(f"[hdbscan] {n_clusters} clusters, {n_noise} noise "
          f"({100*n_noise/len(labels):.0f}%)")

    terms = c_tf_idf(labels, texts, topn=12)

    # sizes + sample titles
    from collections import Counter, defaultdict
    sizes = Counter(labels)
    samples = defaultdict(list)
    for m, l in zip(meta, labels):
        if l != -1 and len(samples[l]) < 3:
            samples[l].append(m["title"][:90])

    # write per-article assignment
    import csv
    with open(os.path.join(OUT, "clusters.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "cluster", "month", "source", "title"])
        for m, l in zip(meta, labels):
            w.writerow([m["id"], int(l), m["month"], m["source"], m["title"]])

    # REPORT
    order = sorted(terms, key=lambda c: -sizes[c])
    lines = [f"# Discovered buckets — India construction corpus",
             f"\n{len(meta)} articles · {n_clusters} clusters · "
             f"{n_noise} unclustered ({100*n_noise/len(labels):.0f}%) · "
             f"min_cluster_size={a.min_cluster_size}\n",
             "Each cluster = a candidate bucket. Read the top terms + samples, "
             "then we collapse these into ~10-12 named parent buckets.\n"]
    for cid in order:
        lines.append(f"\n## Cluster {cid}  ·  n={sizes[cid]}")
        lines.append("**terms:** " + ", ".join(terms[cid]))
        for s in samples[cid]:
            lines.append(f"  - {s}")
    open(os.path.join(OUT, "REPORT.md"), "w").write("\n".join(lines))
    print(f"[out] {OUT}/REPORT.md  ·  clusters.csv  ·  embeddings.npy")

    # compact console preview
    print("\n=== TOP CLUSTERS ===")
    for cid in order[:25]:
        print(f"[{cid:>3}] n={sizes[cid]:>4}  {', '.join(terms[cid][:8])}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-cluster-size", type=int, default=100)
    ap.add_argument("--recluster", action="store_true")
    main(ap.parse_args())
