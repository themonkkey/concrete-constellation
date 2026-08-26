"""Assign every corpus article to one of the 12 locked parent buckets.

Clustered articles inherit their cluster's bucket. The 32% HDBSCAN-noise
articles are assigned to the nearest bucket centroid by cosine. The 3
non-signal clusters (brand/PR, paywall stubs, listing junk) are dropped.

Reads bucket_discovery/{embeddings.npy, meta.json, clusters.csv, taxonomy.json}
(all row-aligned by index). Writes bucket_discovery/assignments.csv.
No torch needed.
"""
import json, csv, numpy as np, collections, os

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bucket_discovery")
emb = np.load(f"{D}/embeddings.npy")                      # already L2-normalized
meta = json.load(open(f"{D}/meta.json"))
tax = json.load(open(f"{D}/taxonomy.json"))
labels = [int(r["cluster"]) for r in csv.DictReader(open(f"{D}/clusters.csv"))]
labels = np.array(labels)
assert len(meta) == len(labels) == emb.shape[0]

drop = set(tax["_noise_drop"]["clusters"])
signal = {pid: info for pid, info in tax.items() if not pid.startswith("_")}
c2p = {c: pid for pid, info in signal.items() for c in info["clusters"]}

# centroid per bucket = mean of its clustered members, renormalized
pids = list(signal)
cent = np.zeros((len(pids), emb.shape[1]), dtype=np.float32)
for i, pid in enumerate(pids):
    mask = np.isin(labels, signal[pid]["clusters"])
    v = emb[mask].mean(axis=0)
    cent[i] = v / (np.linalg.norm(v) + 1e-9)

assign, method, dist = [], [], []
noise_idx = np.where(labels == -1)[0]
# cosine of every noise vector to every centroid, in one matmul
sims_noise = emb[noise_idx] @ cent.T
best = sims_noise.argmax(axis=1)
noise_map = {int(idx): (pids[best[k]], float(sims_noise[k, best[k]]))
             for k, idx in enumerate(noise_idx)}

for i, cl in enumerate(labels):
    if cl in drop:
        assign.append("_drop"); method.append("drop"); dist.append(0.0)
    elif cl in c2p:
        assign.append(c2p[cl]); method.append("cluster"); dist.append(1.0)
    else:  # noise
        pid, s = noise_map[i]
        assign.append(pid); method.append("centroid"); dist.append(round(s, 3))

with open(f"{D}/assignments.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "bucket", "method", "sim", "month", "source", "title"])
    for m, b, mth, s in zip(meta, assign, method, dist):
        w.writerow([m["id"], b, mth, s, m["month"], m["source"], m["title"]])

cnt = collections.Counter(b for b in assign if b != "_drop")
mth = collections.Counter(m for b, m in zip(assign, method) if b != "_drop")
print(f"assigned {sum(cnt.values())} · dropped {assign.count('_drop')} "
      f"({mth['cluster']} from clusters, {mth['centroid']} rescued from noise)\n")
for pid, n in cnt.most_common():
    print(f"  {signal[pid]['name']:<34}{n:>6}")
