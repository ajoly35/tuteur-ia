"""BLS 2025-35 projections x Hosseini-Lichtinger x Boussole grades, plus a French calibration
(occupational structure, demographics, sector mix) and the Althoff-Reichardt (2026) AI scenarios.

Usage: python3 -I analysis.py <scratch_raw_dir> <downloads_dir> <hl_xlsx> <build_data_py> <out_dir>
"""
import importlib.util, json, sys
import numpy as np
import pandas as pd

RAW, DL, HL, BUILD, OUT = sys.argv[1:6]

# ---------- inputs ----------
bls = pd.read_csv(f"{DL}/bls_2025_35_with_exposure_tier.csv", dtype={"soc": str})
adj = pd.read_csv(f"{DL}/bls_table1_12_ai_adjusted_occupations.csv", dtype={"soc": str})
bls["bls_ai_adjusted"] = bls.soc.isin(adj.soc)
TIER = {"Low": 1, "Moderate": 2, "High": 3, "Very high": 4}
bls["tier_n"] = bls.exposure.map(TIER)
bls["growth"] = bls.emp35 / bls.emp25 - 1                    # 10-year growth, fraction
bls["open_rate"] = bls.openings / bls.emp25                  # annual openings / employment
bls["repl_rate_us"] = bls.open_rate - bls.growth / 10        # replacement part (exits + transfers)

hl = pd.read_excel(HL)
hl["soc"] = hl.onetsoccode.str[:7]
hl_soc = hl.groupby("soc").agg(hl_share=("avg_auto_hl_bi", "mean"), hl_expo=("ai_exposure_share", "mean")).reset_index()

# SOC 2018 (BLS) -> SOC 2010 detail; most codes identical. Fallback to broad group (6 chars) then minor group (5 chars).
def lookup(series_by_code, code):
    for n in (7, 6, 5, 4):
        hits = series_by_code[series_by_code.index.str[:n] == code[:n]]
        if len(hits):
            return hits.mean() if hits.dtype != object else hits.mode().iat[0], n
    return np.nan, 0

hl_by = hl_soc.set_index("soc").hl_share
bls["hl_share"], bls["hl_match_len"] = zip(*[lookup(hl_by, c) for c in bls.soc])

# ---------- 1. rank correlation: H-L share vs BLS tier ----------
def spearman(a, b):
    m = a.notna() & b.notna()
    return a[m].rank().corr(b[m].rank()), int(m.sum())

rho, n = spearman(bls.hl_share, bls.tier_n)
rho_w = None
by_tier = bls.groupby("exposure").apply(lambda d: pd.Series({
    "occupations": len(d), "hl_share_mean_empw": np.average(d.hl_share.fillna(d.hl_share.mean()), weights=d.emp25),
    "hl_share_median": d.hl_share.median()})).reindex(TIER.keys()).round(3)

# ---------- Boussole families and grades (same formula as site/boussole/index.html) ----------
spec = importlib.util.spec_from_file_location("bd", BUILD); bd = importlib.util.module_from_spec(spec); spec.loader.exec_module(bd)
hl_onet = hl.set_index("onetsoccode").avg_auto_hl_bi
fams = []
for (key, name, short, group, socs, tier, math, social, *_rest) in bd.F:
    expo = float(hl_onet.loc[socs].mean())
    e, m, d = 1 - min(expo, 0.8) / 0.8, (tier - 1) / 2, (math * social - 1) / 24
    score = round(100 * (0.5 * e + 0.25 * m + 0.25 * d))
    grade = next(b for b, cut in [("A", 65), ("B", 52), ("C", 40), ("D", 28), ("E", -1)] if score > cut)
    fams.append({"k": key, "name": short, "score": score, "grade": grade, "socs": [s[:7] for s in socs]})
fam = pd.DataFrame(fams)

# ---------- 2. French calibration ----------
def eurostat(path):
    d = json.load(open(path)); dims = d["id"]; sizes = d["size"]
    cats = [list(d["dimension"][k]["category"]["index"].keys()) for k in dims]
    rows = []
    for flat, v in d["value"].items():
        i, idx = int(flat), []
        for s in reversed(sizes):
            idx.append(i % s); i //= s
        idx = idx[::-1]
        rows.append({**{dims[j]: cats[j][idx[j]] for j in range(len(dims))}, "value": v})
    return pd.DataFrame(rows)

isco2 = eurostat(f"{RAW}/eu_isco2.json"); isco2 = isco2[isco2.isco08.str.len() == 4].set_index("isco08").value  # OC11 ...
age = eurostat(f"{RAW}/eu_isco1_age.json"); age = age[age.wstatus == "EMP"].pivot_table(index="isco08", columns="age", values="value")
isnace = eurostat(f"{RAW}/eu_isco1_nace.json"); isnace = isnace[isnace.age == "Y_GE15"].pivot_table(index="isco08", columns="nace_r2", values="value")
nace = eurostat(f"{RAW}/eu_nace.json").pivot_table(index="nace_r2", columns="time", values="value")

# SOC 2010 -> ISCO-08 (IBS crosswalk). Many-to-many: take the modal 2-digit ISCO group for each SOC code.
cw = pd.read_stata(f"{RAW}/ibs/onetsoc_to_isco_cws_ibs/soc10_isco08.dta")
cw.columns = [c.lower() for c in cw.columns]
soccol = next(c for c in cw.columns if "soc" in c); iscocol = next(c for c in cw.columns if "isco" in c)
cw["soc"] = cw[soccol].astype(str).str.replace(r"^(\d{2})(\d{4})$", r"\1-\2", regex=True)
cw["isco2"] = "OC" + cw[iscocol].astype(str).str.zfill(4).str[:2]
cw_mode = cw.groupby("soc").isco2.agg(lambda s: s.mode().iat[0])
bls["isco2"], bls["isco_match_len"] = zip(*[lookup(cw_mode, c) for c in bls.soc])
bls["isco1"] = bls.isco2.str[:3]

# (a) occupational structure: French employment by ISCO-2 spread over SOC occupations by US within-group shares
us_by_isco2 = bls.groupby("isco2").emp25.transform("sum")
bls["emp_fr"] = bls.emp25 / us_by_isco2 * bls.isco2.map(isco2)
cover = bls.groupby("isco2").emp_fr.sum().sum() / isco2.sum()

# (b) demographics: end-of-career departures per year = employed aged 55+ / 10 (Metiers 2030 convention: departures
# of those aged 55+ over the next decade), by ISCO-1
dep_rate = ((age["Y55-64"] + age["Y_GE65"].fillna(0)) / age["Y_GE15"] / 10).rename("dep_rate_fr")
bls["dep_rate_fr"] = bls.isco1.map(dep_rate)

# (c) sector mix x sector outlook: French employment growth by NACE section 2014-2024, annualised and carried
# forward 10 years; an ISCO-1 group's growth = its French sector weights x those sector growth rates.
g_sec = (nace["2024"] / nace["2014"]) ** (10 / 10) - 1          # 10-year growth by section
g_sec = g_sec.drop(["TOTAL", "NRP"], errors="ignore")
w = isnace.drop(columns=["TOTAL", "NRP"], errors="ignore")
w = w.div(w.sum(axis=1), axis=0)
g_total_fr = nace.loc["TOTAL", "2024"] / nace.loc["TOTAL", "2014"] - 1
# demographic anchor: change in the population aged 20-64, 2025 to 2035 (Eurostat EUROPOP2023 baseline),
# i.e. constant employment rates by age; sectors keep their past growth relative to the total
pj = json.load(open(f"{RAW}/eu_proj.json")); nage = len(pj["dimension"]["age"]["category"]["index"])
pv = [pj["value"][str(i)] for i in range(2 * nage)]
g_demog = sum(pv[1::2]) / sum(pv[0::2]) - 1
cols = g_sec.index.intersection(w.columns)
g_isco1_fr = g_demog + (w[cols] * (g_sec[cols] - g_total_fr)).sum(axis=1)
# Shift-share with the BLS National Employment Matrix (occupation x sector, 2025 and 2035):
#   US growth of occupation o = sum_s w_US(s|o) * [(1 + g_US(s)) * (1 + sigma(o,s)) - 1]
# where g_US(s) is sector growth and sigma(o,s) the change in o's share of sector s (technology, incl. AI).
# France: keep sigma(o,s) from BLS; replace w_US(s|o) by French sector weights and g_US(s) by French sector growth.
NAICS2NACE = {"110000": "A", "210000": "B", "220000": "DE", "230000": "F", "31-330": "C", "420000": "G", "44-450": "G",
              "48-490": "H", "510000": "J", "520000": "K", "530000": "L", "540000": "M", "550000": "M", "560000": "N",
              "610000": "P", "620000": "Q", "710000": "R", "720000": "I", "810000": "S", "900000": "O", "TE1100": "SE"}
mx = pd.read_excel(f"{RAW}/bls/matrix.xlsx", sheet_name="Matrix", dtype={"Industry code": str, "Occupation code": str})
mx = mx[mx["Industry code"].isin(NAICS2NACE)].rename(columns={"Occupation code": "soc", "2025 Employment": "e25", "2035 Employment": "e35"})
mx["sec"] = mx["Industry code"].map(NAICS2NACE)
sec_tot = mx[mx.soc == "00-0000"].groupby("sec")[["e25", "e35"]].sum()
mx = mx[mx.soc.isin(bls.soc)].groupby(["soc", "sec"])[["e25", "e35"]].sum().reset_index()
mx = mx.join(sec_tot, on="sec", rsuffix="_sec")
mx["g_sec_us"] = mx.e35_sec / mx.e25_sec - 1
mx["sigma"] = (mx.e35 / mx.e35_sec) / (mx.e25 / mx.e25_sec) - 1
mx.loc[mx.e25 <= 0, "sigma"] = 0
mx["w_us"] = mx.e25 / mx.groupby("soc").e25.transform("sum")
mx["isco1"] = mx.soc.map(bls.set_index("soc").isco1)
# French sector growth: demographic anchor + each sector's 2014-2024 growth relative to total employment
# national accounts (consistent series; the LFS has a 2021 break)
nama = eurostat(f"{RAW}/eu_nama.json").pivot_table(index="nace_r2", columns="time", values="value")
nama.loc["DE"] = nama.loc[["D", "E"]].sum()
g_total_na = nama.loc["TOTAL", "2024"] / nama.loc["TOTAL", "2014"] - 1
g_fr_sec = g_demog + (nama["2024"] / nama["2014"] - 1 - g_total_na)
g_fr_sec["SE"] = g_demog
# French sector weights within an occupation: US weights x (French / US weight of that sector in the ISCO-1 group)
wfr = isnace.copy(); wfr["DE"] = wfr[["D", "E"]].sum(axis=1)
wfr = wfr[[c for c in set(NAICS2NACE.values()) if c in wfr.columns]]
wfr = wfr.div(wfr.sum(axis=1), axis=0).stack().rename("w_fr_k").reset_index().rename(columns={"level_1": "sec", "nace_r2": "sec"})
wfr.columns = ["isco1", "sec", "w_fr_k"]
ws = mx[mx.sec != "SE"].groupby(["isco1", "sec"]).e25.sum()
wus_k = (ws / ws.groupby(level=0).transform("sum")).rename("w_us_k").reset_index()
mx = mx.merge(wfr, on=["isco1", "sec"], how="left").merge(wus_k, on=["isco1", "sec"], how="left")
mx["ratio"] = np.where(mx.sec == "SE", 1.0, (mx.w_fr_k / mx.w_us_k).replace([np.inf], np.nan)).astype(float)
mx["ratio"] = mx.ratio.fillna(1.0).clip(0, 10)
mx["w_fr"] = mx.w_us * mx.ratio
mx["w_fr"] = mx.w_fr / mx.groupby("soc").w_fr.transform("sum")
mx["g_sec_fr"] = mx.sec.map(g_fr_sec)
mx["c_us"] = mx.w_us * ((1 + mx.g_sec_us) * (1 + mx.sigma) - 1)
mx["c_fr"] = mx.w_fr * ((1 + mx.g_sec_fr) * (1 + mx.sigma) - 1)
mx["c_us_ind"] = mx.w_us * mx.g_sec_us
# variant B: French structure and demography, but the BLS sector outlook relative to the US total
g_us_total = sec_tot.e35.sum() / sec_tot.e25.sum() - 1
mx["g_sec_fr_b"] = g_demog + (mx.g_sec_us - g_us_total)
mx["c_fr_b"] = mx.w_fr * ((1 + mx.g_sec_fr_b) * (1 + mx.sigma) - 1)
sh = mx.groupby("soc")[["c_us", "c_fr", "c_fr_b", "c_us_ind"]].sum()
bls["growth_us_check"] = bls.soc.map(sh.c_us)
bls["growth_fr_trend"] = bls.soc.map(sh.c_fr)
bls["growth_fr"] = bls.soc.map(sh.c_fr_b)          # central French variant used on the site
bls["us_industry_effect"] = bls.soc.map(sh.c_us_ind)
shift_check = float((bls.growth_us_check - bls.growth).abs().median())

# Exits from BLS Table 1.10, rescaled to the French age structure:
#   French exit rate of o = US exit rate of o x (French 55+/10 departure rate of its ISCO-1 group / US mean exit rate of the group)
t10 = pd.read_excel(f"{RAW}/bls/occupation.xlsx", sheet_name="Table 1.10", header=1, dtype=str)
t10 = t10.rename(columns={t10.columns[1]: "soc", t10.columns[7]: "exit_rate", t10.columns[8]: "transfer_rate"})
t10 = t10[t10.soc.str.match(r"^\d{2}-\d{4}$", na=False)].set_index("soc")
bls["exit_us"] = bls.soc.map(pd.to_numeric(t10.exit_rate, errors="coerce")) / 100
bls["transfer_us"] = bls.soc.map(pd.to_numeric(t10.transfer_rate, errors="coerce")) / 100
exit_us_k = bls.groupby("isco1").apply(lambda d: np.average(d.exit_us.fillna(d.exit_us.mean()), weights=d.emp25))
bls["exit_fr"] = bls.exit_us * bls.isco1.map(dep_rate) / bls.isco1.map(exit_us_k)
# French "postes a pourvoir" per year (Metiers 2030 definition): net creation + end-of-career departures
bls["open_rate_fr"] = bls.growth_fr / 10 + bls.exit_fr
bls["open_rate_fr_trend"] = bls.growth_fr_trend / 10 + bls.exit_fr
# US on the same definition (growth + labour-force exits, no occupational transfers)
bls["open_rate_us_exits"] = bls.growth / 10 + bls.exit_us

# ---------- 3. Althoff-Reichardt long-run AI scenarios (3-digit SOC 2010) ----------
def minor(soc):
    return "15-11" if soc.startswith("15-12") else soc[:5]
AR_CODES = set(pd.read_csv(f"{RAW}/ar/occ_moderate.csv", dtype={"soc_code": str}).soc_code)
bls["ar_code"] = [minor(c) if minor(c) in AR_CODES else (c[:4] + "0" if c[:4] + "0" in AR_CODES else None) for c in bls.soc]
for scen in ["slow", "moderate", "rapid"]:
    ar = pd.read_csv(f"{RAW}/ar/occ_{scen}.csv", dtype={"soc_code": str}).set_index("soc_code")
    bls[f"ar_emp_{scen}"] = bls.ar_code.map(ar.pct_ch_emp_share_genai)
    bls[f"ar_wage_{scen}"] = bls.ar_code.map(ar.pct_ch_mean_wage_genai)
ar_mod = pd.read_csv(f"{RAW}/ar/occ_moderate.csv", dtype={"soc_code": str})
hl3 = bls.groupby("ar_code").apply(lambda d: np.average(d.hl_share.fillna(d.hl_share.mean()), weights=d.emp25))
ar_mod["hl_share"] = ar_mod.soc_code.map(hl3)
rho_ar, n_ar = spearman(ar_mod.hl_share, ar_mod.pct_ch_emp_share_genai)
rho_ar_w, _ = spearman(ar_mod.hl_share, ar_mod.pct_ch_mean_wage_genai)
tier3 = bls.groupby("ar_code").apply(lambda d: np.average(d.tier_n, weights=d.emp25))
ar_mod["tier"] = ar_mod.soc_code.map(tier3)
rho_ar_tier, _ = spearman(ar_mod.tier, ar_mod.pct_ch_emp_share_genai)

# ---------- 4. by Boussole grade, employment-weighted ----------
occ = bls.set_index("soc")
def agg(socs, wcol):
    d = occ.loc[[s for s in socs if s in occ.index]]
    if d.empty:
        d = occ[occ.index.str[:6].isin([s[:6] for s in socs])]
    wts = d[wcol]
    def wavg(c):
        m = d[c].notna()
        return np.average(d.loc[m, c], weights=wts[m]) if m.any() else np.nan
    return pd.Series({
        "us_growth_pct": 100 * (d.emp35.sum() / d.emp25.sum() - 1),
        "us_openings_pct": 100 * d.openings.sum() / d.emp25.sum(),
        "share_high_vhigh_pct": 100 * wts[d.tier_n >= 3].sum() / wts.sum(),
        "bls_ai_adjusted_pct": 100 * wts[d.bls_ai_adjusted].sum() / wts.sum(),
        "fr_growth_pct": 100 * wavg("growth_fr"),
        "fr_postes_pct": 100 * wavg("open_rate_fr"),
        "fr_growth_trend_pct": 100 * wavg("growth_fr_trend"),
        "us_postes_pct": 100 * wavg("open_rate_us_exits"),
        "ar_emp_moderate_pct": 100 * wavg("ar_emp_moderate"),
        "ar_emp_rapid_pct": 100 * wavg("ar_emp_rapid"),
        "ar_wage_moderate_pct": 100 * wavg("ar_wage_moderate"),
        "n_occ": len(d)})

fam_tab = fam.join(fam.socs.apply(lambda s: agg(s, "emp25")))
grade_rows = []
for g, d in fam.groupby("grade"):
    socs = sorted({s for l in d.socs for s in l})
    us = agg(socs, "emp25"); fr = agg(socs, "emp_fr")
    grade_rows.append({"grade": g, "families": len(d), "occupations": int(us.n_occ),
                       "us_growth_pct": us.us_growth_pct, "us_openings_pct": us.us_openings_pct,
                       "share_high_vhigh_pct": us.share_high_vhigh_pct, "bls_ai_adjusted_pct": us.bls_ai_adjusted_pct,
                       "us_postes_pct": us.us_postes_pct, "fr_growth_pct": fr.fr_growth_pct, "fr_growth_trend_pct": fr.fr_growth_trend_pct, "fr_postes_pct": fr.fr_postes_pct,
                       "ar_emp_moderate_pct": us.ar_emp_moderate_pct, "ar_emp_rapid_pct": us.ar_emp_rapid_pct,
                       "ar_wage_moderate_pct": us.ar_wage_moderate_pct})
grade_tab = pd.DataFrame(grade_rows).set_index("grade").round(1)

# whole economy benchmarks
bench = {"us_growth_pct": 100 * (bls.emp35.sum() / bls.emp25.sum() - 1),
         "us_openings_pct": 100 * bls.openings.sum() / bls.emp25.sum(),
         "fr_growth_pct": 100 * np.average(bls.growth_fr.fillna(0), weights=bls.emp_fr.fillna(0)),
         "fr_demog_20_64_2025_35_pct": 100 * g_demog,
         "fr_growth_trend_pct": 100 * np.average(bls.growth_fr_trend.fillna(0), weights=bls.emp_fr.fillna(0)),
         "fr_postes_pct": 100 * np.average(bls.open_rate_fr.fillna(bls.open_rate_fr.mean()), weights=bls.emp_fr.fillna(0)),
         "us_postes_pct": 100 * np.average(bls.open_rate_us_exits.fillna(bls.open_rate_us_exits.mean()), weights=bls.emp25),
         "fr_dep_rate_pct": 100 * float(((age["Y55-64"] + age["Y_GE65"]) / age["Y_GE15"] / 10).loc["TOTAL"]),
         "fr_total_growth_2014_24_pct": 100 * g_total_fr}

# ---------- outputs ----------
bls.to_csv(f"{OUT}/occupations_merged.csv", index=False)
fam_tab.drop(columns="socs").to_csv(f"{OUT}/by_family.csv", index=False)
grade_tab.to_csv(f"{OUT}/by_grade.csv")
diag = {
    "spearman_hl_vs_bls_tier": round(rho, 3), "n": n,
    "hl_share_by_tier": by_tier.reset_index().to_dict("records"),
    "spearman_hl_vs_AR_emp_moderate_3digit": round(rho_ar, 3), "n_3digit": n_ar,
    "spearman_hl_vs_AR_wage_moderate_3digit": round(rho_ar_w, 3),
    "spearman_bls_tier_vs_AR_emp_moderate_3digit": round(rho_ar_tier, 3),
    "hl_match_exact_pct": round(100 * (bls.hl_match_len == 7).mean(), 1),
    "isco_match_exact_pct": round(100 * (bls.isco_match_len == 7).mean(), 1),
    "fr_employment_covered_pct": round(100 * cover, 1),
    "dep_rate_fr_by_isco1_pct": (100 * dep_rate).round(2).to_dict(),
    "shift_share_check_median_abs_error_pts": round(100 * shift_check, 3),
    "g_sector_fr_10y_pct": (100 * g_fr_sec).round(1).to_dict(),
    "g_sector_us_10y_pct": (100 * (sec_tot.e35 / sec_tot.e25 - 1)).round(1).to_dict(),
    "us_industry_effect_empw_pct": round(100 * np.average(bls.us_industry_effect.fillna(0), weights=bls.emp25), 2),
    "exit_us_mean_pct": round(100 * np.average(bls.exit_us.fillna(0), weights=bls.emp25), 2),
    "benchmarks": {k: round(v, 2) for k, v in bench.items()},
}
json.dump(diag, open(f"{OUT}/diagnostics.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(diag, indent=1, ensure_ascii=False))
print(grade_tab.to_string())
print(fam_tab.drop(columns="socs").sort_values("score", ascending=False).round(1).to_string(index=False))

# ---------- 5. data file for the Boussole site ----------
r1 = lambda x: None if pd.isna(x) else round(float(x), 1)
proj = {"fams": {row.k: {"us_g": r1(row.us_growth_pct), "us_o": r1(row.us_openings_pct), "fr_g": r1(row.fr_growth_pct),
                          "fr_o": r1(row.fr_postes_pct), "us_p": r1(row.us_postes_pct), "adj": r1(row.bls_ai_adjusted_pct),
                          "ar_m": r1(row.ar_emp_moderate_pct), "ar_r": r1(row.ar_emp_rapid_pct)}
                 for row in fam_tab.itertuples()},
        "meta": {"rho_tier": round(rho, 2), "us_g": r1(bench["us_growth_pct"]), "fr_g": r1(bench["fr_growth_pct"]),
                 "fr_o": r1(bench["fr_postes_pct"]), "us_p": r1(bench["us_postes_pct"]), "demog": r1(bench["fr_demog_20_64_2025_35_pct"]),
                 "grades": {g: {k: r1(v) for k, v in row.items()} for g, row in grade_tab.iterrows()}}}
with open(f"{OUT}/projections.js", "w", encoding="utf-8") as fh:
    fh.write("window.BOUSSOLE_PROJ=" + json.dumps(proj, ensure_ascii=False, separators=(",", ":")) + ";\n")
