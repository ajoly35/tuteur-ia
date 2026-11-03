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
