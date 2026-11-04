"""Build site/boussole/reussite.js: admission chances by pair of bac specialities (Parcoursup 2025)
and success rates by bac mention (licence and DUT cohorts, MESR-SIES) for each Boussole family.

Usage: python3 build_reussite.py <psup_doublettes.json> <reussite_licence.csv> <reussite_dut.csv> <out.js>
Sources (data.enseignementsup-recherche.gouv.fr):
  fr-esr-parcoursup-enseignements-de-specialite-bacheliers-generaux-3  (bac 2025, bac general only)
  fr-esr-parcours-et-reussite-des-bacheliers-en-licence                 (passage L2: cohort 2014; licence: cohort 2012)
  fr-esr-parcours-et-reussite-des-bacheliers-en-dut                     (passage DUT2: cohort 2014; DUT: cohort 2013)
"""
import json
import sys

import pandas as pd

PSUP, LIC, DUT, OUT = sys.argv[1:5]

# Boussole family -> Parcoursup 2025 "libelle_complet" (level 1 = group of programmes, level 2 = programme)
ADM = {
 "maths": ["1 - Licence Mathématiques", "1 - Licence Mathématiques et informatique", "1 - Licence MASS"],
 "info": ["1 - Licence Informatique"],
 "info_court": ["2 - BUT prod - Informatique", "2 - BUT prod - Réseaux et télécommunications", "2 - BUT prod - Métiers du multimédia et de l'internet",
                "2 - BTS serv - Services informatiques aux organisations", "2 - BTS prod - Cybersécurité, Informatique et réseaux, ELectronique", "2 - BUT serv - Science des données"],
 "inge": ["1 - Ingé", "2 - Autres - C.M.I - Cursus de Master en Ingénierie"],
 "physique": ["1 - Licence Physique", "1 - Licence Chimie", "1 - Licence Physique et chimie", "1 - Licence Formation générale aux métiers de l ingénieur",
              "1 - Licence Mécanique, Génie mécanique, Ingénierie mécanique", "1 - Licence Electronique, Génie électrique, EEA", "1 - Licence Pluri Sciences fondamentales et applications"],
 "eco": ["1 - Licence Sciences économiques", "1 - Licence Sciences de gestion", "1 - Licence AES", "1 - Licence Pluri Sciences économiques - Gestion", "1 - Licence Pluri Droit - Sciences éco - AES"],
 "commerce_pge": ["2 - Comm - Formation des écoles de commerce et de management Bac + 5"],
 "bachelor": ["2 - Comm - Formation des écoles de commerce et de management Bac + 3", "2 - Comm - Formation des écoles de commerce et de management Bac + 4"],
 "compta": ["2 - BTS serv - Comptabilité et gestion", "2 - BUT serv - Gestion des entreprises et des administrations", "2 - DCG - Diplôme de Comptabilité et de Gestion"],
 "vente": ["2 - BTS serv - Management Commercial Opérationnel", "2 - BTS serv - Négociation et digitalisation de la Relation Client", "2 - BUT serv - Techniques de commercialisation", "2 - BTS serv - Commerce International"],
 "banque": ["2 - BTS serv - Banque", "2 - BTS serv - Assurance", "2 - BTS serv - Professions immobilières"],
 "admin": ["2 - BTS serv - Gestion de la PME", "2 - BTS serv - Support à l'action managériale", "2 - BUT serv - Gestion administrative et commerciale des organisations", "2 - BUT serv - Carrières juridiques"],
 "droit": ["1 - Licence Sciences juridiques"],
 "iep": ["1 - ScPo", "1 - Licence Sciences politiques"],
 "socio_psy": ["1 - Licence Psychlogie, Sciences cognitives", "1 - Licence Sociologie, Démographie", "1 - Licence Sciences de l'éducation"],
 "lettres": ["1 - Licence Histoire", "1 - Licence Géographie", "1 - Licence Langues et littératures françaises", "1 - Licence Philosophie, Epistémologie", "1 - Licence Sciences du langage - Linguistique"],
 "langues": ["1 - Licence LEA", "1 - Licence Langues et littératures étrangères"],
 "journalisme": ["1 - Licence Sciences de l information et de la communication", "2 - BUT serv - Information communication", "2 - BTS serv - Communication"],
 "arts": ["1 - Art", "1 - Licence Arts"],
 "cpes": ["1 - CyPES"],
 "prepa_sci": ["1 - CPGE S"], "prepa_eco": ["1 - CPGE ECG"], "prepa_lit": ["1 - CPGE L"],
 "infirmier": ["2 - DE san - D.E Infirmier"],
 "sante": ["1 - PASS", "1 - Licence L.AS"],
 "paramedical": ["2 - DE san - D.E Ergothérapeute", "2 - DE san - D.E Psychomotricien", "2 - DE san - D.E Pédicure-Podologue", "2 - DE san - Certificat de capacité d'Orthophoniste",
                 "2 - DE san - Certificat de capacité d'Orthoptiste", "2 - DE san - D.E manipulateur/trice en électroradiologie médicale", "2 - DE san - DTS Imagerie médicale et radiologie thérapeutique", "2 - DE san - D.E Audioprothésiste"],
 "bio": ["1 - Licence Sciences de la vie, biologie, santé", "1 - Licence Sciences de l univers, de la terre, de l espace", "1 - Licence Pluri Sciences de la vie, de la santé, de la terre et de l univers"],
 "labo": ["2 - BUT prod - Génie biologique", "2 - BTS prod - Bioanalyses en laboratoire de contrôle", "2 - BTS serv - Biologie médicale", "2 - BTS prod - Biotechnologie en recherche et en production", "2 - DE san - D.E Technicien de Laboratoire Médical"],
 "social": ["1 - DE soc"],
 "aide": ["2 - BTS serv - Economie sociale familiale", "2 - BTS serv - Services et prestations des secteurs sanitaire et social", "2 - BTS serv - Diététique et nutrition", "2 - BTS serv - Opticien-Lunetier", "2 - BUT serv - Carrières sociales"],
 "staps": ["1 - Licence STAPS"],
 "elec": ["2 - BTS prod - Electrotechnique", "2 - BUT prod - Génie électrique et informatique industrielle", "2 - BTS prod - Maintenance des systèmes", "2 - BUT prod - Génie industriel et maintenance",
          "2 - BTS prod - Fluide, énergie, domotique", "2 - BUT prod - Métiers de la Transition et de l'Efficacité Énergétiques"],
 "industrie": ["2 - BUT prod - Génie mécanique et productique", "2 - BTS prod - Conception de produits industriels", "2 - BUT prod - Mesures physiques", "2 - BUT prod - Chimie",
               "2 - BUT prod - Génie chimique génie des procédés", "2 - BTS prod - Pilotage des procédés", "2 - BUT prod - Qualité, logistique industrielle et organisation", "2 - BUT prod - Science et génie des matériaux"],
 "btp": ["2 - BUT prod - Génie civil", "2 - BTS prod - Bâtiment", "2 - BTS prod - Travaux publics", "2 - BTS prod - Management économique de la construction", "1 - Licence Génie civil"],
 "agri": ["1 - BTS agri"],
 "tourisme": ["2 - BTS serv - Tourisme", "2 - DEUST - Accueil d'excellence en tourisme"],
 "logistique": ["2 - BTS serv - Gestion des transports et logistique associée", "2 - BUT serv - Management de la Logistique et des Transports"],
}

# Boussole family -> success data: ("lic", secteurs disciplinaires) or ("dut", DUT names)
SUCC = {
 "maths": ("lic", ["Mathématiques", "Mathématique et informatique", "Mathématiques appliquées et sciences sociales"]),
 "info": ("lic", ["Informatique"]),
 "info_court": ("dut", ["Informatique", "Réseaux et télécommunications", "Métiers du multimédia et de l'internet", "Statistique et informatique décisionnelle"]),
 "physique": ("lic", ["Physique", "Chimie", "Physique et chimie", "Formation générale aux métiers de l'ingénieur", "Mécanique, génie mécanique", "Électronique, génie électrique", "Pluridisciplinaire sciences fondamentales et applications"]),
 "eco": ("lic", ["Sciences économiques", "Sciences de gestion", "Administration économique et sociale", "Pluridisciplinaire sciences économiques et gestion"]),
 "compta": ("dut", ["Gestion des entreprises et administrations"]),
 "vente": ("dut", ["Techniques de commercialisation"]),
 "admin": ("dut", ["Gestion administrative et commerciale des organisations", "Carrières juridiques"]),
 "droit": ("lic", ["Sciences juridiques", "Pluridisciplinaire droit, sciences politiques"]),
 "iep": ("lic", ["Sciences politiques"]),
 "socio_psy": ("lic", ["Psychologie", "Sociologie, démographie", "Sciences de l'éducation"]),
 "lettres": ("lic", ["Histoire", "Géographie", "Langues et littératures françaises", "Philosophie, épistémologie", "Sciences du langage, linguistique"]),
 "langues": ("lic", ["Langues étrangères appliquées", "Langues et littératures étrangères"]),
 "journalisme": ("lic", ["Sciences de l'information et la communication"]),
 "arts": ("lic", ["Arts"]),
 "bio": ("lic", ["Sciences de la vie", "Sciences de l'univers", "Pluridisciplinaire sciences de la vie, de la santé, de la terre et de l'univers"]),
 "labo": ("dut", ["Génie biologique"]),
 "aide": ("dut", ["Carrières sociales"]),
 "staps": ("lic", ["STAPS"]),
 "elec": ("dut", ["Génie électrique et informatique industrielle", "Génie industriel et maintenance", "Génie thermique et énergie"]),
 "industrie": ("dut", ["Génie mécanique et productique", "Mesures physiques", "Chimie", "Génie chimique - Génie des procédés", "Qualité, logistique industrielle et organisation", "Sciences et génie des matériaux"]),
 "btp": ("dut", ["Génie civil - Construction durable"]),
 "logistique": ("dut", ["Gestion logistique et transport"]),
}

SHORT = {"Art": "Arts", "Biologie/Ecologie": "Biologie-écologie", "Histoire-Géographie, Géopolitique et Sciences politiques": "HGGSP",
         "Humanités, Littérature et Philosophie": "HLP", "Langues, littératures et cultures étrangères et régionales": "LLCER",
         "Littérature et langues et cultures de l'Antiquité": "LLCA", "Mathématiques Spécialité": "Maths", "Numérique et Sciences Informatiques": "NSI",
         "Physique-Chimie Spécialité": "Physique-chimie", "Sciences Economiques et Sociales Spécialité": "SES",
         "Sciences de l'ingénieur et sciences physiques": "SI", "Sciences de la vie et de la Terre Spécialité": "SVT",
         "Éducation physique, pratiques et culture sportives": "EPPCS"}
MENTION = {"Passable premier groupe": "P", "Passable deuxième groupe": "P", "Assez bien": "AB", "Bien": "B", "Très bien": "TB"}
GENERAL = {"BAC L", "BAC ES", "BAC S"}

def key(d):
    return "|".join(sorted(SHORT[s] for s in d))

# ---- admission by doublette ----
rows = json.load(open(PSUP, encoding="utf-8"))
ADM = {k: [l + " - Ensemble regroupement de formations" if l.startswith("1 - ") else l for l in v] for k, v in ADM.items()}
labels = {r["libelle_complet"] for r in rows}
missing = [l for v in ADM.values() for l in v if l not in labels]
assert not missing, missing
spec_totals = {}
adm = {}
for k, libs in ADM.items():
    agg = {}
    for r in rows:
        if r["libelle_complet"] in libs:
            a = agg.setdefault(key(r["doublette"]), [0, 0, 0])
            a[0] += r["voeux"] or 0; a[1] += int(r["propositions_d_admissions"] or 0); a[2] += r["acceptations"] or 0
    tot = [sum(v[i] for v in agg.values()) for i in range(3)]
    adm[k] = {"d": {d: v for d, v in agg.items() if v[0] > 0}, "t": tot}
for r in rows:
    if r["niveau_d_agregation"] == "0":
        spec_totals[key(r["doublette"])] = r["voeux"]

# ---- success by mention (bac général only for licence; DUT: all bacs général + techno, by mention) ----
def success(df, cols, frame):
    out = {}
    df = df.copy()
    df["m"] = df.mention_bac_lib.map(MENTION)
    for m, d in list(df.groupby("m")) + [("all", df)]:
        n1, n2 = d[cols["n1"]].sum(), d[cols["n2"]].sum()
        if n1 < 100 or n2 < 100:
            continue
        out[m] = {"n": int(n1), "l2": round(100 * d[cols["l2"]].sum() / n1), "red": round(100 * d[cols["red"]].sum() / n1),
                  "dip": round(100 * d[cols["dip"]].sum() / n2)}
    return out

lic = pd.read_csv(LIC, sep=";")
lic = lic[lic.serie_bac_lib.isin(GENERAL)]
dut = pd.read_csv(DUT, sep=";")
dut = dut[dut.serie_bac_lib.isin(GENERAL | {"BAC STMG", "BAC technologique hors STMG"})]
succ = {}
for k, (typ, names) in SUCC.items():
    if typ == "lic":
        d = lic[lic.sect_disciplinaire_lib.isin(names)]
        assert d.sect_disciplinaire_lib.nunique() == len(names), (k, set(names) - set(d.sect_disciplinaire_lib))
        s = success(d, {"n1": "effectif_neobacheliers_passage", "n2": "effectif_neobacheliers_reussite", "l2": "passage_en_l2_1_an",
                        "red": "redoublement_en_l1", "dip": "reussite_3_4_ans"}, "lic")
    else:
        d = dut[dut.dut_lib.isin(names)]
        assert d.dut_lib.nunique() == len(names), (k, set(names) - set(d.dut_lib))
        s = success(d, {"n1": "effectif_neobacheliers_passage", "n2": "effectif_neobacheliers_reussite", "l2": "passage_en_dut2_1_an",
                        "red": "redoublement_en_dut1", "dip": "reussite_2_3_ans"}, "dut")
    succ[k] = {"type": typ, **s}

data = {"adm": adm, "succ": succ, "specs": sorted(set(SHORT.values())), "spec_totals": spec_totals,
        "meta": {"psup": 2025, "lic_l2": 2014, "lic_dip": 2012, "dut_l2": 2014, "dut_dip": 2013}}
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("window.BOUSSOLE_REUSSITE=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("ok", OUT)
for k in ADM:
    t = adm[k]["t"]; s = succ.get(k, {})
    print(f"{k:13s} voeux {t[0]:7d} prop {100*t[1]/max(t[0],1):5.1f}%  succ {s.get('type','-')} all {s.get('all')} TB {s.get('TB')}")

# =====================================================================================================
# Recent national rates and per-university rates (MESR-SIES, Note Flash 2025-29, session 2024)
# Usage (second step): python3 build_reussite.py ... <out.js> <sies_nationaux.xlsx> <sies_etablissements.xlsx> <data.js>
# =====================================================================================================
if len(sys.argv) > 5:
    import re
    import unicodedata
    NAT, ETAB, DATAJS = sys.argv[5:8]
    DISC = {"droit": "Droit, Sc. politiques", "iep": "Droit, Sc. politiques", "eco": "Economie, AES",
            "lettres": "Arts, lettres, langues, SHS", "langues": "Arts, lettres, langues, SHS", "socio_psy": "Arts, lettres, langues, SHS",
            "journalisme": "Arts, lettres, langues, SHS", "arts": "Arts, lettres, langues, SHS",
            "maths": "Sciences-santé", "info": "Sciences-santé", "physique": "Sciences-santé", "bio": "Sciences-santé", "staps": "STAPS"}
    DISC_FR = {"Droit, Sc. politiques": "droit et science politique", "Economie, AES": "économie, gestion et AES",
               "Arts, lettres, langues, SHS": "arts, lettres, langues et sciences humaines", "Sciences-santé": "sciences et santé", "STAPS": "STAPS"}
    SPEC = {"HIST_GE": "HGGSP", "LIT_PHI": "HLP", "LLCER": "LLCER", "MATHS": "Maths", "PHY_CHI": "Physique-chimie", "SES": "SES",
            "SVT": "SVT", "NUMERIQ": "NSI", "SC_INGE": "SI", "ART_PLA": "Arts", "EPS": "EPPCS"}
    MEN2 = {"Très bien": "TB", "Bien": "B", "Assez bien": "AB", "Passable premier groupe": "P"}
    clean = lambda s: re.sub(r"\s+", " ", str(s)).strip()

    def table(path, sheet):
        t = pd.read_excel(path, sheet, header=None)
        hdr = [clean(h) for h in t.iloc[2]]
        t = t.iloc[3:].copy(); t.columns = hdr
        return t
    num = lambda v: float(v) if isinstance(v, (int, float)) and not pd.isna(v) else None

    dev = table(NAT, "Devenir cohorte 2023")
    dev["Discipline en L1"] = dev["Discipline en L1"].map(clean)
    reu = table(NAT, "Reussite - 3ou4 ans - tous")
    reu["Discipline en L1"] = reu["Discipline en L1"].map(clean)
    nat = {}
    for disc in set(DISC.values()):
        d, r = dev[dev["Discipline en L1"] == disc], reu[reu["Discipline en L1"] == disc]
        out = {"by_m": {}, "by_d": {}}
        def row(x):
            return {"n": int(x["Inscrits en L1"]), "l2": round(num(x["Taux de passage en L2"])), "red": round(num(x["Taux de redoublement en L1"])),
                    "reo": round(num(x["Taux de réorientation"])), "out": round(num(x["Taux de sortie de l'enseignement supérieur"]))}
        for _, x in d.iterrows():
            car, mod = clean(x["Caractéristiques des étudiants"]), clean(x["Modalités"])
            if num(x["Inscrits en L1"]) is None or num(x["Taux de passage en L2"]) is None:
                continue
            if car == "Ensemble":
                out["all"] = row(x)
            elif car == "Mention obtenue au baccalauréat" and mod in MEN2:
                out["by_m"][MEN2[mod]] = row(x)
            elif car == "Série du baccalauréat" and "/" in mod:
                a, b = [SPEC.get(s.strip()) for s in mod.split("/")]
                if a and b and num(x["Inscrits en L1"]) >= 200:
                    out["by_d"]["|".join(sorted([a, b]))] = row(x)
        for _, x in r.iterrows():
            car, mod = clean(x["Caractéristiques"]), clean(x["Modalités"])
            v = num(x["Réussite cumulée en 4 ans (%)"])
            if v is None:
                continue
            if car == "Ensemble":
                out.setdefault("all", {})["dip"] = round(v)
            elif car == "Mention obtenue au baccalauréat" and mod in MEN2:
                out["by_m"].setdefault(MEN2[mod], {})["dip"] = round(v)
        nat[disc] = out

    # ---- per university ----
    def norm(s):
        s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
        return re.sub(r"\s+", " ", s)
    # Parcoursup establishment name -> SIES establishment (first rule that matches wins; private institutes never match)
    RULES_U = [
        (r"catholique|uco|ices|ircom|cnam|ileps|institut saint-pie|isfec|fac libre|faculte libre|facultes libres|protestant|enseignement prive|ecm|ecole de commerce|lycee|esslil|inalco|eivp|ecole du numerique", None),
        (r"dauphine", "PSL"), (r"departement universitaire de sciences d'agen", "DE BORDEAUX"), (r"roscoff - sorbonne", "SORBONNE UNIVERSITE"),
        (r"aix-marseille", "AIX-MARSEILLE"), (r"avignon", "AVIGNON"), (r"paris-saclay|paris saclay", "PARIS SACLAY"),
        (r"cergy", "CERGY"), (r"lyon 3|jean moulin", "LYON 3"), (r"lyon 1|claude bernard", "LYON 1"), (r"lyon 2|lumiere", "LYON 2"),
        (r"reims|urca|eisine|esireims", "REIMS"), (r"champollion", "CHAMPOLLION"), (r"la rochelle", "LA ROCHELLE"),
        (r"le mans|du mans", "LE MANS"), (r"nantes universite", "NANTES"), (r"^sorbonne universite", "SORBONNE UNIVERSITE"),
        (r"jean monnet|saint-etienne", "SAINT ETIENNE"), (r"universite de lille", "LILLE"), (r"universite angers", "ANGERS"),
        (r"bordeaux montaigne", "BORDEAUX 3"), (r"universite de bordeaux", "DE BORDEAUX"), (r"bourgogne", "DIJON"),
        (r"clermont auvergne", "CLERMONT"), (r"cote d'azur", "COTE AZUR"), (r"grenoble alpes", "GRENOBLE"), (r"gustave eiffel", "GUSTAVE EIFFEL"),
        (r"le havre", "LE HAVRE"), (r"franche-comte|marie et louis pasteur", "BESANCON"), (r"assas", "ASSAS"),
        (r"paris 1 pantheon", "PARIS 1"), (r"paris 8", "PARIS 8"), (r"paris cite", "PARIS CITE"), (r"nanterre", "NANTERRE"),
        (r"upec|est-creteil|est- creteil", "CRETEIL"), (r"paul valery|montpellier 3", "MONTPELLIER 3"), (r"universite de montpellier", "MONTPELLIER"),
        (r"polytechnique hauts-de-france", "POLYTECHNIQUE"), (r"savoie mont blanc", "SAVOIE"), (r"sorbonne nouvelle", "PARIS 3"),
        (r"sorbonne paris nord", "SORBONNE PARIS NORD"), (r"toulouse 2|jean jaures", "TOULOUSE 2"), (r"toulouse capitole|toulouse school of economics", "TOULOUSE 1"),
        (r"toulouse iii|paul sabatier", "TOULOUSE 3"), (r"universite d'amiens|insset", "AMIENS"), (r"artois", "ARTOIS"), (r"evry", "EVRY"),
        (r"orleans", "ORLEANS"), (r"universite de brest", "BREST"), (r"universite de bretagne sud", "BRETAGNE SUD"), (r"caen", "CAEN"),
        (r"corte", "CORSE"), (r"guyane", "GUYANE"), (r"universite de la reunion", "REUNION"), (r"limoges", "LIMOGES"), (r"lorraine", "LORRAINE"),
        (r"mayotte", "MAYOTTE"), (r"mulhouse|uha business", "MULHOUSE"), (r"nimes", "NIMES"), (r"pau et des pays", "PAU"), (r"perpignan", "PERPIGNAN"),
        (r"poitiers", "POITIERS"), (r"rennes 2", "RENNES 2"), (r"universite de rennes", "RENNES 1"), (r"rouen", "ROUEN"),
        (r"strasbourg", "STRASBOURG"), (r"toulon", "TOULON"), (r"universite de tours", "TOURS"), (r"versailles", "VERSAILLES"),
        (r"universite de la polynesie", "POLYNESIE"), (r"antilles", "ANTILLES"), (r"littoral", "LITTORAL"), (r"nouvelle-caledonie", "NOUVELLE-CALEDONIE"),
    ]
    # canonical key -> regex on the SIES name (several SIES spellings per university across sheets)
    SIES_KEY = {"AIX-MARSEILLE": r"AIX-MARSEILLE", "AVIGNON": r"AVIGNON", "PARIS SACLAY": r"PARIS SACLAY", "CERGY": r"CERGY", "LYON 3": r"LYON 3",
                "LYON 1": r"LYON 1", "LYON 2": r"LYON 2", "REIMS": r"REIMS", "CHAMPOLLION": r"CHAMPOLLION", "LA ROCHELLE": r"LA ROCHELLE",
                "LE MANS": r"LE MANS", "NANTES": r"UNIVERSITE NANTES", "SORBONNE UNIVERSITE": r"^SORBONNE UNIVERSITE", "SAINT ETIENNE": r"SAINT ETIENNE",
                "LILLE": r"UNIVERSITE LILLE", "ANGERS": r"ANGERS", "BORDEAUX 3": r"BORDEAUX 3", "DE BORDEAUX": r"DE BORDEAUX", "DIJON": r"DIJON",
                "CLERMONT": r"CLERMONT", "COTE AZUR": r"COTE AZUR", "GRENOBLE": r"GRENOBLE", "GUSTAVE EIFFEL": r"GUSTAVE EIFFEL", "LE HAVRE": r"LE HAVRE",
                "BESANCON": r"BESANCON", "ASSAS": r"ASSAS", "PARIS 1": r"PARIS 1\b", "PARIS 8": r"PARIS 8", "PARIS CITE": r"PARIS CITE",
                "NANTERRE": r"NANTERRE", "CRETEIL": r"CRETEIL", "MONTPELLIER 3": r"MONTPELLIER 3", "MONTPELLIER": r"MONTPELLIER$",
                "POLYTECHNIQUE": r"POLYTECHNIQUE", "SAVOIE": r"SAVOIE", "PARIS 3": r"PARIS 3", "SORBONNE PARIS NORD": r"PARIS 13|SORBONNE PARIS NORD",
                "TOULOUSE 2": r"TOULOUSE 2", "TOULOUSE 1": r"TOULOUSE 1", "TOULOUSE 3": r"TOULOUSE 3", "AMIENS": r"AMIENS", "ARTOIS": r"ARTOIS",
                "EVRY": r"EVRY", "ORLEANS": r"ORLEANS", "BREST": r"BREST", "BRETAGNE SUD": r"BRETAGNE SUD", "CAEN": r"CAEN", "CORSE": r"CORSE",
                "GUYANE": r"GUYANE", "REUNION": r"REUNION", "LIMOGES": r"LIMOGES", "LORRAINE": r"LORRAINE", "MAYOTTE": r"MAYOTTE",
                "MULHOUSE": r"MULHOUSE", "NIMES": r"NIMES", "PAU": r"\bPAU\b", "PERPIGNAN": r"PERPIGNAN", "POITIERS": r"POITIERS",
                "RENNES 2": r"RENNES 2", "RENNES 1": r"RENNES 1|DE RENNES", "ROUEN": r"ROUEN", "STRASBOURG": r"STRASBOURG", "TOULON": r"TOULON",
                "TOURS": r"TOURS", "VERSAILLES": r"VERSAILLES", "POLYNESIE": r"POLYNESIE", "ANTILLES": r"ANTILLES", "LITTORAL": r"LITTORAL",
                "NOUVELLE-CALEDONIE": r"CALEDONIE", "PSL": r"PARIS SCIENCES LETTRES"}
    def univ_rows(sheet, cols):
        t = table(ETAB, sheet)
        t = t[t["Discipline en L1"].notna()]
        t["Nom établissement en L1"] = t["Nom établissement en L1"].map(clean); t["Discipline en L1"] = t["Discipline en L1"].map(clean)
        out = {}
        for key, pat in SIES_KEY.items():
            sel = t[t["Nom établissement en L1"].str.contains(pat, regex=True)]
            for _, x in sel.iterrows():
                vals = {k: num(x[c]) for k, c in cols.items()}
                if vals.get("n") is None or vals.get("rate") is None:
                    continue
                out.setdefault(key, {})[x["Discipline en L1"]] = {k: (round(v) if v is not None else None) for k, v in vals.items()}
        return out
    u_l2 = univ_rows("Devenir cohorte 2023 VA", {"n": "Inscrits en L1", "rate": "Taux de passage en L2", "sim": "Taux de passage en L2 simulé",
                                                "va": "Passage en L2 - Valeur Ajoutée (en points)"})
    u_dip = univ_rows("Réussite 3ou4ans discip VA", {"n": "Inscrits en L1", "rate": "Réussite en 3 ou 4 ans (taux observé)",
                                                    "va": "Valeur ajoutée réussite en 3 ou 4 ans (en points)"})
    univ = {}
    for key in set(u_l2) | set(u_dip):
        for disc in set(u_l2.get(key, {})) | set(u_dip.get(key, {})):
            a, b = u_l2.get(key, {}).get(disc), u_dip.get(key, {}).get(disc)
            univ.setdefault(key, {})[disc] = {"l2": a and a["rate"], "l2va": a and a["va"], "l2n": a and a["n"],
                                              "dip": b and b["rate"], "dipva": b and b["va"]}
    js = open(DATAJS, encoding="utf-8").read()
    Dd = json.loads(js[js.index("=") + 1: js.rstrip().rindex(";")])
    etab_map, unmatched = {}, set()
    for o in Dd["offers"]:
        n = norm(o[1])
        if "univ" not in n and not re.search(r"champollion|cy |urca|eisine|esireims|insset|uha|ecole universitaire|dauphine", n):
            continue
        key = next((k for pat, k in RULES_U if re.search(pat, n)), "?")
        if key == "?":
            unmatched.add(o[1])
        elif key and key in univ:
            etab_map[o[1]] = key
    data["nat"] = {d: v for d, v in nat.items()}
    data["disc"] = DISC; data["disc_fr"] = DISC_FR
    data["univ"] = univ; data["etab"] = etab_map
    data["meta"].update({"nat_l2": 2023, "nat_dip": 2020, "source_nat": "MESR-SIES, Note Flash 2025-29"})
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("window.BOUSSOLE_REUSSITE=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("universities with data", len(univ), "| Parcoursup establishments matched", len(etab_map), "| unmatched university-like names", len(unmatched))
    for n in sorted(unmatched):
        print("   unmatched:", n)
    for disc, v in nat.items():
        print(disc, v.get("all"), {m: v["by_m"].get(m) for m in ["P", "TB"]}, len(v["by_d"]), "doublettes")
