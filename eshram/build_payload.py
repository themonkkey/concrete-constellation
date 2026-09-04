#!/usr/bin/env python3
"""Build the eShram constellation payload from the EILA aggregates.

Implements the design-panel spec (2026-09-04): 36 state hubs (unsized anchors),
~822 district satellites (calibrated sizes), 100 directed inter-state corridors
(82 >= 2,000 movers + 18 forced), 78 origin-state -> district edges, 31,740
worker-proportional motes (1 mote = 10,000 registrations, state-calibrated,
Hamilton allocation, own gender + occupation group), a 2,445-dot belt for the
dump/dashboard gap, a 7-stop occupation-group scrub axis, and geo targets from
the 2024 Survey of India / LGD district boundaries. Assertions fail the build.

  python3 eshram/build_payload.py            # writes eshram/eshram_data.json + counts.json
"""
import csv, json, math, os, re, sys, collections
import pandas as pd

A = "/Volumes/EILA/PIF /eshram/agg"
SCRATCH = "/private/tmp/claude-501/-Users-thesinghaa/f2bf941b-f825-4a73-9bae-c060f58f9e63/scratchpad"
SHP = f"{SCRATCH}/shp/91/DISTRICT_BOUNDARY.shp"
MATCH = f"{SCRATCH}/match_table.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eshram_data.json")
COUNTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "counts.json")

K = 10_000
UNITS_PER_DEG, LON0, LAT0 = 36.0, 82.5, 22.5
slug = lambda s: re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
clamp = lambda v, lo, hi: max(lo, min(hi, v))
tpar = lambda fem: clamp((fem - 0.50) / 0.17, -1, 1)          # parity pivot
tlit = lambda s: clamp((s - 0.03) / 0.39, 0, 1)

# ---- spelling twins merged INTO the canonical row, legacy rows dropped ----
MERGE = {("CHHATTISGARH", "KABEERDHAM"): "KABIRDHAM",
         ("CHHATTISGARH", "DAKSHIN BASTAR DANTEWADA"): "DANTEWADA",
         ("CHHATTISGARH", "BALODABAZAR-BHATAPARA"): "BALODA BAZAR",
         ("CHHATTISGARH", "GAURELA-PENDRA-MARWAHI"): "GAURELLA PENDRA MARWAHI",
         ("SIKKIM", "SOUTH"): "SOUTH DISTRICT",
         ("WEST BENGAL", "NORTH 24 PARGANAS"): "24 PARAGANAS NORTH",
         ("WEST BENGAL", "MALDA"): "MALDAH",
         ("WEST BENGAL", "PASCHIM MEDINIPUR"): "MEDINIPUR WEST",
         ("WEST BENGAL", "COOCH BEHAR"): "COOCHBEHAR",
         ("MAHARASHTRA", "AHILYANAGAR"): "AHMEDNAGAR"}
DROP_BELOW = 100
STATE_FOLD = {"PUDUCHERRY": "PONDICHERRY"}

GROUPS = ["Agriculture", "Construction & mining", "Domestic & care", "Manufacturing",
          "Artisanal", "Services & urban", "Miscellaneous"]
GMAP = {}
for i, names in enumerate([
    ["AGRICULTURE"],
    ["CONSTRUCTION", "MINING"],
    ["DOMESTIC AND HOUSEHOLD WORKERS", "HEALTHCARE", "BEAUTY & WELLNESS"],
    ["APPAREL", "CAPITAL GOODS & MANUFACTURING", "LEATHER INDUSTRY WORKS", "ELECTRONICS & HW",
     "TOBACCO INDUSTRY", "FOOD INDUSTRY", "GEM & JEWELLERY", "PRINTING", "GLASS & CERAMICS",
     "TOOL MAKERS AND RELATED WORKERS"],
    ["HANDICRAFTS & CARPETS", "TEXTILE & HANDLOOM", "WOOD & CARPENTRY", "MUSICAL INSTRUMENTS",
     "CARPENTERS AND JOINERS"],
    ["AUTOMOBILE & TRANSPORTATION", "EDUCATION", "TOURISM & HOSPITALITY",
     "OFFICE ADMINISTRATION & FACILITY MANAGEMENT", "RETAIL", "ORGANISED RETAIL", "PRIVATE SECURITY",
     "PROFESSIONALS", "SERVICE", "BFSI", "BANKING FINANCIAL SERVICES & INSURANCE",
     "BANKING, FINANCIAL SERVICES & INSURANCE"],
    ["MISCELLANEOUS", "OTHERS", "NOT PROVIDED"]]):
    for n in names: GMAP[n] = i
TYP = ["Agricultural", "Construction", "Domestic/Care", "Services/Urban", "Manufacturing", "Artisanal"]
WORK_HUE = ["#a9ab54", "#dc9064", "#a498e5", "#50b1dc", "#d887ae", "#51bb9a", "#787885"]
# typology class -> hue index in the same 7-hue table (Services/Urban -> 5, Manufacturing -> 3, Artisanal -> 4)
TYP_HUE = [0, 1, 2, 5, 3, 4]
AGE7 = ["<18", "18-25", "26-35", "36-45", "46-55", "56-59", "60+"]
EDU5 = {"NOT LITERATE": 0,
        "LITERATE WITHOUT FORMAL SCHOOLING": 1, "BELOW PRIMARY": 1, "PRIMARY": 1,
        "MIDDLE": 2,
        "SECONDARY": 3, "HIGHER SECONDARY": 3,
        "DIPLOMA/CERTIFICATE COURSE": 4, "GRADUATE": 4, "POST-GRADUATE AND ABOVE": 4,
        "TECHNICAL DEGREE IN AGRICULTURE": 4, "TECHNICAL DEGREE IN CRAFTS": 4,
        "TECHNICAL DEGREE IN ENGINEERING / TECHNOLOGY": 4, "TECHNICAL DEGREE IN MEDICINE": 4,
        "TECHNICAL DEGREE IN OTHER SUBJECT": 4}
STATE_PT = {"UTTAR PRADESH": (80.78, 27.14), "BIHAR": (86.12, 25.90), "MAHARASHTRA": (75.43, 18.82),
    "WEST BENGAL": (88.06, 24.39), "MADHYA PRADESH": (79.39, 23.97), "RAJASTHAN": (73.83, 26.63),
    "KARNATAKA": (75.53, 15.03), "GUJARAT": (71.99, 22.42), "ODISHA": (84.48, 20.19),
    "ANDHRA PRADESH": (79.62, 15.90), "TAMIL NADU": (78.35, 10.82), "JHARKHAND": (85.17, 23.66),
    "CHHATTISGARH": (81.51, 20.94), "ASSAM": (90.76, 26.05), "KERALA": (76.43, 10.54),
    "PUNJAB": (75.58, 31.03), "HARYANA": (76.05, 29.29), "TELANGANA": (79.30, 17.88),
    "DELHI": (77.12, 28.64), "JAMMU AND KASHMIR": (74.93, 33.70), "UTTARAKHAND": (79.32, 30.09),
    "HIMACHAL PRADESH": (77.35, 31.82), "TRIPURA": (91.65, 23.74), "MANIPUR": (93.87, 24.76),
    "MEGHALAYA": (91.26, 25.57), "ARUNACHAL PRADESH": (95.00, 28.06), "NAGALAND": (94.56, 26.12),
    "GOA": (74.10, 15.35), "MIZORAM": (92.87, 23.23), "CHANDIGARH": (76.78, 30.73),
    "SIKKIM": (88.46, 27.60), "PONDICHERRY": (79.81, 10.92),
    "THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU": (70.93, 20.72), "LADAKH": (77.66, 34.72),
    "ANDAMAN AND NICOBAR ISLANDS": (92.49, 10.71), "LAKSHADWEEP": (73.68, 10.81)}
proj = lambda lon, lat: (round((lon - LON0) * UNITS_PER_DEG, 2), round(-(lat - LAT0) * UNITS_PER_DEG, 2))

def rd(name, **kw):
    df = pd.read_csv(f"{A}/{name}", **kw).rename(columns={"count": "cnt"})
    for c in ("state", "current_state", "permanent_state"):
        if c in df: df[c] = df[c].replace(STATE_FOLD)
    return df

def canon(df, sc="state", dc="district"):
    """Apply MERGE to a district column, then collapse duplicate keys by summing counts."""
    if dc not in df: return df
    df = df.copy()
    df[dc] = [MERGE.get((s, d), d) for s, d in zip(df[sc], df[dc])]
    return df

# ------------------------------------------------------------------ load
ds = canon(rd("district_summary.csv"))
cal = rd("calibration_factors.csv"); FAC = dict(zip(cal.state, cal.factor))
OFF = dict(zip(cal.state, cal.official_total))
dog = canon(rd("district_occupation_gender.csv"))
do = canon(rd("district_occupation.csv"))
edu = canon(rd("district_education.csv"))
ageb = canon(rd("district_age_band.csv"))
mm = rd("migration_matrix.csv")
dmo = canon(rd("district_migrant_origin.csv"), "current_state", "current_district")
rq6 = canon(rd("rq6_district_types.csv"))

DUMP_TOTAL = int(ds.total.sum())
assert DUMP_TOTAL == 341_854_283, DUMP_TOTAL

# drop legacy rows, then merge twins (sum numeric columns)
legacy = ds[ds.total < DROP_BELOW]
dropped_regs = int(legacy.total.sum())
ds = ds[ds.total >= DROP_BELOW]
num = ["total", "female", "male", "other_gender", "differently_abled"]
ds = ds.groupby(["state", "district"], as_index=False).agg({**{c: "sum" for c in num}, "mean_age": "mean"})
ds["pct_female"] = ds.female / ds.total
n_districts = len(ds)
keys = set(zip(ds.state, ds.district))
assert int(ds.total.sum()) + dropped_regs == DUMP_TOTAL

# ------------------------------------------------------------------ geometry
import geopandas as gpd
shp = gpd.read_file(SHP).to_crs(4326)
shp["pt"] = shp.geometry.representative_point()
fix = lambda s: str(s).upper().replace(">", "A").replace("|", "I").replace("<", "A").replace("&", "AND")
shp["st_fix"] = shp.STATE_UT.map(fix)
match = {(r[0], r[1]): r[3] for r in json.load(open(MATCH))}
by_name = collections.defaultdict(list)
for _, r in shp.iterrows(): by_name[str(r.DISTRICT)].append(r)
def state_like(a, b):
    a, b = fix(a), fix(b)
    return a == b or a.replace(" ", "")[:6] == b.replace(" ", "")[:6]
geo = {}; tiers = collections.Counter()
for (s, d) in keys:
    nm = match.get((s, d)) or match.get((s, MERGE.get((s, d), d)))
    if not nm:
        # twins were merged: try the pre-merge spellings that map to this canonical name
        for (ms, md), tgt in MERGE.items():
            if ms == s and tgt == d and (ms, md) in match: nm = match[(ms, md)]
    rows = by_name.get(nm, []) if nm else []
    rows = [r for r in rows if state_like(r.st_fix, s)] or rows
    if rows:
        p = rows[0].pt; geo[(s, d)] = (p.x, p.y, True); tiers["matched"] += 1
    else:
        tiers["fallback"] += 1
# fallback: state point + golden-angle offset
fb_i = collections.Counter()
for (s, d) in sorted(keys):
    if (s, d) in geo: continue
    lon, lat = STATE_PT[s]; i = fb_i[s]; fb_i[s] += 1
    r = (8 + 3 * math.sqrt(i)) / UNITS_PER_DEG; th = i * 2.39996
    geo[(s, d)] = (lon + r * math.cos(th), lat + r * math.sin(th), False)

# ------------------------------------------------------------------ groups & cells
occs = set(dog.primary_occupation)
unmapped = occs - set(GMAP)
assert not unmapped, f"unmapped occupations: {unmapped}"
dog["g"] = dog.primary_occupation.map(GMAP)
assert int(dog["cnt"].sum()) == DUMP_TOTAL
gsum = dog.groupby("g")["cnt"].sum()
assert int(gsum.sum()) == DUMP_TOTAL

# per node x group: total and female (all genders in denominator)
def grp_series(df, keycols):
    t = df.groupby(keycols + ["g"])["cnt"].sum()
    f = df[df.gender == "FEMALE"].groupby(keycols + ["g"])["cnt"].sum()
    out = collections.defaultdict(dict)
    for idx, n in t.items():
        k = idx[:-1] if len(keycols) > 1 else (idx[0],); g = idx[-1]
        fem = float(f.get(idx, 0)) / n if n else 0
        key = k if len(keycols) > 1 else k[0]
        out[key][GROUPS[g]] = [round(tpar(fem), 4), int(n), round(fem, 4)]
    return out
d_series = grp_series(dog, ["state", "district"])
s_series = grp_series(dog, ["state"])
nat = dog.groupby("g")["cnt"].sum(); natf = dog[dog.gender == "FEMALE"].groupby("g")["cnt"].sum()
composite = [[GROUPS[g], round(tpar(natf.get(g, 0) / nat[g]), 4), int(nat[g]), round(natf.get(g, 0) / nat[g], 4)] for g in range(7)]

# ------------------------------------------------------------------ hubs
st = ds.groupby("state").agg(total=("total", "sum"), female=("female", "sum"), nd=("district", "count"))
edu["e5"] = edu.education.map(EDU5)
lit_d = edu[edu.education == "NOT LITERATE"].groupby(["state", "district"])["cnt"].sum()
tot_d = edu.groupby(["state", "district"])["cnt"].sum()
lit_s = edu[edu.education == "NOT LITERATE"].groupby("state")["cnt"].sum(); tot_s = edu.groupby("state")["cnt"].sum()
edu5_d = edu.dropna(subset=["e5"]).groupby(["state", "district", "e5"])["cnt"].sum()
edu5_s = edu.dropna(subset=["e5"]).groupby(["state", "e5"])["cnt"].sum()
age_d = ageb.groupby(["state", "district", "age_band"])["cnt"].sum(); age_s = ageb.groupby(["state", "age_band"])["cnt"].sum()
inter = mm[(mm.permanent_state != mm.current_state) & (mm["cnt"] > 0)]
inflow = inter.groupby("current_state")["cnt"].sum(); outflow = inter.groupby("permanent_state")["cnt"].sum()
sid = lambda s: "s:" + slug(s)
buckets = []
for s, r in st.iterrows():
    lit = float(lit_s.get(s, 0)) / float(tot_s.get(s, 1))
    lon, lat = STATE_PT[s]; gx, gy = proj(lon, lat)
    outs = inter[inter.permanent_state == s].nlargest(5, "cnt"); ins = inter[inter.current_state == s].nlargest(5, "cnt")
    buckets.append({"id": sid(s), "name": s.title().replace(" And ", " & "), "n": int(round(r.total * FAC[s])),
        "n_raw": int(r.total), "factor": round(float(FAC[s]), 4), "official": int(OFF[s]),
        "health": round(tpar(r.female / r.total), 4), "fem": round(r.female / r.total, 4),
        "lit": round(lit, 4), "litT": round(tlit(lit), 4), "gx": gx, "gy": gy, "r": 5,
        "in": int(inflow.get(s, 0)), "out": int(outflow.get(s, 0)), "net": int(inflow.get(s, 0) - outflow.get(s, 0)),
        "top_out": [[sid(x.current_state), int(x.cnt)] for x in outs.itertuples()],
        "top_in": [[sid(x.permanent_state), int(x.cnt)] for x in ins.itertuples()],
        "age7": [int(age_s.get((s, b), 0)) for b in AGE7],
        "edu5": [int(edu5_s.get((s, float(i)), 0)) for i in range(5)],
        "nd": int(r.nd), "matched": True})
assert len(buckets) == 36, len(buckets)
CAL_TOTAL = sum(b["n"] for b in buckets)

# ------------------------------------------------------------------ satellites
top_d = collections.defaultdict(list)
for (s, d), grp in do.groupby(["state", "district"]):
    t = grp["cnt"].sum(); g2 = grp.nlargest(5, "cnt")
    top_d[(s, d)] = [[x.primary_occupation.title(), round(x.cnt / t, 3)] for x in g2.itertuples()]
occ_fem = collections.defaultdict(lambda: [0, 0])
for x in dog.itertuples():
    k = (x.state, x.district, x.primary_occupation); occ_fem[k][1] += x.cnt
    if x.gender == "FEMALE": occ_fem[k][0] += x.cnt
mig_t = dmo.groupby(["current_state", "current_district"])["cnt"].sum()
mig_in = dmo[dmo.permanent_state != dmo.current_state].groupby(["current_state", "current_district"])["cnt"].sum()
orig = collections.defaultdict(list)
for (s, d), grp in dmo[dmo.permanent_state != dmo.current_state].groupby(["current_state", "current_district"]):
    orig[(s, d)] = [[sid(x.permanent_state), int(x.cnt)] for x in grp.nlargest(3, "cnt").itertuples()]
typ = {(x.state, x.district): (TYP.index(x.dest_type) if x.dest_type in TYP else -1, float(x.LQ)) for x in rq6.itertuples()}
did = lambda s, d: f"d:{slug(s)}:{slug(d)}"
clusters = []; pts = {}
for i, r in enumerate(ds.sort_values(["state", "district"]).itertuples()):
    s, d = r.state, r.district; lon, lat, ok = geo[(s, d)]; gx, gy = proj(lon, lat); pts[did(s, d)] = (gx, gy)
    lit = float(lit_d.get((s, d), 0)) / float(tot_d.get((s, d), 1))
    tt, lq = typ.get((s, d), (-1, 0.0))
    n_cal = int(round(r.total * FAC[s]))
    top5 = [[o, sh, round(occ_fem[(s, d, o.upper())][0] / occ_fem[(s, d, o.upper())][1], 3) if occ_fem[(s, d, o.upper())][1] else None] for o, sh in top_d[(s, d)]]
    clusters.append({"id": did(s, d), "cluster": i, "parent": sid(s), "n": n_cal, "n_raw": int(r.total),
        "health": round(tpar(r.pct_female), 4), "fem": round(float(r.pct_female), 4),
        "lit": round(lit, 4), "litT": round(tlit(lit), 4), "typ": tt, "lq": round(lq, 2),
        "top3": top5[:3], "top5": top5,
        "mig": round(float(mig_in.get((s, d), 0)) / float(mig_t.get((s, d), 1)), 4),
        "origins": orig[(s, d)][:3],
        "age7": [int(age_d.get((s, d, b), 0)) for b in AGE7],
        "edu5": [int(edu5_d.get((s, d, float(k)), 0)) for k in range(5)],
        "mean_age": round(float(r.mean_age), 1), "abled": round(r.differently_abled / r.total, 4),
        "terms": [d.title(), s.title(), (TYP[tt] if tt >= 0 else "unclassified")] + [o.lower() for o, _, _ in top5[:3]],
        "gx": gx, "gy": gy, "matched": ok, "r": round(max(1.2, 0.0065 * math.sqrt(n_cal)), 2)})
# nearest-neighbour distance for the dust radius cap
ids = list(pts); P = [pts[k] for k in ids]
for c in clusters:
    x, y = pts[c["id"]]; best = 1e9
    for (px, py) in P:
        if px == x and py == y: continue
        dd = (px - x) ** 2 + (py - y) ** 2
        if dd < best: best = dd
    c["nn"] = round(math.sqrt(best), 2) if best < 1e9 else 40.0

# ------------------------------------------------------------------ motes (Hamilton, two stage)
MOTES = int(round(CAL_TOTAL / K))
quota = [c["n"] / K for c in clusters]; base = [math.floor(q) for q in quota]
rem = MOTES - sum(base)
order = sorted(range(len(clusters)), key=lambda i: quota[i] - base[i], reverse=True)
for i in order[:rem]: base[i] += 1
assert sum(base) == MOTES
cells = collections.defaultdict(list)   # district -> [(g, sign, count)]
for x in dog.itertuples():
    if x.gender not in ("FEMALE", "MALE"): continue
    cells[(x.state, x.district)].append((int(x.g), 10 if x.gender == "FEMALE" else -10, int(x.cnt)))
dust = {}; motes_f = motes_m = 0; gcount = collections.Counter(); zero = 0
for c, q in zip(clusters, base):
    c["motes"] = q
    if q == 0: zero += 1; continue
    s, d = c["id"], None
    st_, dt_ = next((k for k in cells if did(*k) == c["id"]), (None, None))
    cl = cells.get((st_, dt_), []); tot = sum(n for _, _, n in cl)
    if not cl or tot == 0: continue
    qs = [q * n / tot for _, _, n in cl]; b = [math.floor(v) for v in qs]; r = q - sum(b)
    for j in sorted(range(len(cl)), key=lambda j: qs[j] - b[j], reverse=True)[:r]: b[j] += 1
    arr = []
    for (g, sg, _), k in zip(cl, b):
        arr += [[sg, g]] * k
        if sg > 0: motes_f += k
        else: motes_m += k
        gcount[g] += k
    dust[c["id"]] = arr
assert sum(len(v) for v in dust.values()) == MOTES, (sum(len(v) for v in dust.values()), MOTES)

# ------------------------------------------------------------------ edges
inter = inter.copy()
back = {(a, b): int(n) for a, b, n in zip(inter.permanent_state, inter.current_state, inter["cnt"])}
GMAX = 73928.0
def w_of(gross): return round(clamp(math.log10(max(gross, 2000) / 2000) / math.log10(GMAX / 2000), 0, 1), 4)
edges = []; seen = set()
for x in inter.itertuples():
    if x.cnt >= 2000:
        edges.append({"a": sid(x.permanent_state), "b": sid(x.current_state), "n": int(x.cnt),
            "back": back.get((x.current_state, x.permanent_state), 0), "forced": False}); seen.add(x.permanent_state)
for s in st.index:
    if s in seen: continue
    top = inter[inter.permanent_state == s].nlargest(1, "cnt")
    for x in top.itertuples():
        edges.append({"a": sid(s), "b": sid(x.current_state), "n": int(x.cnt),
            "back": back.get((x.current_state, s), 0), "forced": True})
for e in edges: e["w"] = w_of(e["n"] + e["back"])
inter_movers = int(inter["cnt"].sum()); drawn = sum(e["n"] for e in edges if not e["forced"])
edges_in = []
for x in dmo[(dmo.permanent_state != dmo.current_state) & (dmo["cnt"] >= 2000)].itertuples():
    if (x.current_state, x.current_district) not in keys: continue
    edges_in.append({"a": sid(x.permanent_state), "b": did(x.current_state, x.current_district), "n": int(x.cnt), "w": w_of(int(x.cnt))})

# ------------------------------------------------------------------ belt
gap_total = DUMP_TOTAL - CAL_TOTAL
belt_n = int(round(gap_total / K))
segs = []
for b in buckets:
    gap = b["n_raw"] - b["n"]; segs.append([b["id"], int(gap), max(0, int(round(gap / K)))])
diff = belt_n - sum(x[2] for x in segs)
segs.sort(key=lambda x: -x[1]); segs[0][2] += diff

# ------------------------------------------------------------------ write
meta = {"K": K, "unitsPerDeg": UNITS_PER_DEG, "lon0": LON0, "lat0": LAT0,
        "calibrated_total": CAL_TOTAL, "dump_total": DUMP_TOTAL, "dropped_legacy_rows": int(len(legacy)),
        "dropped_legacy_regs": dropped_regs, "dashboard_date": "2026-06-30",
        "boundary": "Survey of India / LGD 2024 district boundaries (mapgen)",
        "matched": tiers["matched"], "fallback": tiers["fallback"], "n_districts": n_districts,
        "national_fem": round(float(ds.female.sum() / ds.total.sum()), 4),
        "national_lit": round(float(lit_s.sum() / tot_s.sum()), 4),
        "interstate_movers": inter_movers, "corridors_drawn_share": round(drawn / inter_movers, 4),
        "edges_in_share": round(sum(e["n"] for e in edges_in) / inter_movers, 4),
        "size_floor_regs": int((1.2 / 0.0065) ** 2), "size_floor_districts": sum(1 for c in clusters if c["r"] <= 1.2),
        "motes_f": motes_f, "motes_m": motes_m, "motes_zero_districts": zero, "groups_motes": [gcount[g] for g in range(7)]}
data = {"generated": "2026-09-04", "total": DUMP_TOTAL, "months": GROUPS, "axis": GROUPS, "meta": meta,
        "buckets": buckets, "clusters": clusters, "bucket_edges": edges, "edges_in": edges_in,
        "series": {sid(s): v for s, v in s_series.items()},
        "cluster_series": {did(*k): v for k, v in d_series.items() if k in keys},
        "composite": composite, "dust": dust, "belt": belt_n, "belt_segments": segs,
        "modes": ["women", "work", "literacy", "corridors"], "work_hue": WORK_HUE, "typ_hue": TYP_HUE,
        "typ_names": TYP, "group_names": GROUPS}
json.dump(data, open(OUT, "w"), separators=(",", ":"))
counts = {"hubs": len(buckets), "districts": len(clusters), "corridors": len(edges),
          "corridors_forced": sum(e["forced"] for e in edges), "edges_in": len(edges_in), "motes": MOTES,
          "belt": belt_n, "dust_points": MOTES + belt_n, "geo_matched": tiers["matched"], "geo_fallback": tiers["fallback"],
          "payload_kb": os.path.getsize(OUT) // 1024, **{k: meta[k] for k in ("calibrated_total", "dump_total", "motes_f", "motes_m", "groups_motes", "size_floor_districts", "corridors_drawn_share", "edges_in_share")}}
json.dump(counts, open(COUNTS, "w"), indent=1)
print(json.dumps(counts, indent=1))
