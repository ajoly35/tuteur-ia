// Voice guide for the Boussole page. Relies on globals from the page script:
// D (data), byScore, findOffers, psupLink, renderList, open, TIER, $.
(function () {
  const P = paramsURL();
  const fields = { profil: "v-profil", classe: "v-classe", lieu: "v-lieu", interets: "v-int" };
  for (const [k, id] of Object.entries(fields)) if (P[k]) $(id).value = P[k];
  let question = P.question || "";

  // Resolve a family from a key, or loosely from a name the agent said.
  function famille(x) {
    const s = String(x || "").toLowerCase().trim();
    if (!s) return null;
    return D.fams.find((f) => f.k === s)
      || D.fams.find((f) => (f.n + " " + f.s).toLowerCase().includes(s))
      || D.fams.find((f) => s.split(/\s+/).some((w) => w.length > 3 && (f.n + " " + f.s + " " + f.jobs).toLowerCase().includes(w)));
  }
  function resume(f) {
    return {
      cle: f.k, nom: f.n, note: f.band[0], sens_note: f.band[3], score_sur_100: f.score,
      taches_IA_sur_10: f.sur10, type_de_metier: TIER[f.tier], maths_sur_5: f.math, contact_humain_sur_5: f.social,
      emploi_30_mois_pourcent: f.ins ? Math.round(f.ins.emploi) : null,
      salaire_median_net_mois: f.ins ? f.ins.salaire : null, niveau_insertion: f.ins ? f.ins.niveau : null,
      metiers: f.jobs, conseil: f.note, nb_formations_parcoursup: f.nb,
    };
  }

  const clientTools = {
    // Real Parcoursup 2025 courses for a family near a place, with access rate.
    chercher_formations: async ({ famille: fam, lieu }) => {
      const f = famille(fam);
      if (!f) return "Famille inconnue. Clés possibles : " + D.fams.map((x) => x.k).join(", ");
      let list = findOffers(f.i, lieu || "", 5);
      let note = "";
      if (!list.length && lieu) { list = findOffers(f.i, "", 5); note = `Aucune formation trouvée pour « ${lieu} » ; voici les plus grandes en France.`; }
      return JSON.stringify({
        famille: resume(f), remarque: note,
        formations: list.map((o) => ({ formation: o[4], etablissement: o[1], ville: o[2], departement: o[3], places: o[5],
          taux_acces_pourcent: o[6] >= 0 ? o[6] : null, public: !!o[8], lien: psupLink(o[7]) })),
      });
    },
    // Opens the family card on the page so the pupil sees what the guide is talking about.
    afficher_famille: async ({ famille: fam }) => {
      const f = famille(fam);
      if (!f) return "Famille inconnue. Clés possibles : " + D.fams.map((x) => x.k).join(", ");
      const q = $("q"); if (q) q.value = "";
      open = f.i;
      renderList();
      const el = document.querySelector(`.fam[data-i="${f.i}"]`);
      if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); el.classList.add("flash"); setTimeout(() => el.classList.remove("flash"), 2500); }
      return JSON.stringify({ affiche: true, famille: resume(f) });
    },
    // Ranked list of families, optionally filtered by type (Université, BTS / BUT, Prépa...).
    classement_familles: async ({ type } = {}) => {
      const t = String(type || "").toLowerCase();
      const rows = byScore.filter((f) => !t || f.g.toLowerCase().includes(t));
      return JSON.stringify(rows.map((f) => ({ cle: f.k, nom: f.s, type: f.g, note: f.band[0], salaire: f.ins ? f.ins.salaire : null })));
    },
  };

  // Opening line after "Bonjour ! Je suis Claire...": says what Claire is for, then builds on what the
  // form already gave (class, interests) instead of asking for it again, with a first question fitted to the age.
  function accrocher(v, q) {
    const classe = v.classe !== "inconnue" ? v.classe : "";
    const gouts = v.interets !== "inconnus" ? v.interets : "";
    if (v.profil === "parent") {
      return "Je suis là pour vous aider à y voir clair sur l'orientation de votre enfant. "
        + (q ? `Vous m'avez demandé : « ${q} ». On en parle. ` : "")
        + (classe ? `Votre enfant est en ${classe} : qu'est-ce qui vous préoccupe le plus ?` : "En quelle classe est votre enfant, et qu'est-ce qui vous préoccupe ?");
    }
    const intro = "Je suis là pour t'aider à réfléchir à la suite : ce qui te plaît, les métiers qui te tentent, et les formations qui y mènent. ";
    if (q) return intro + `Tu m'as demandé : « ${q} ». On en parle.` + (classe ? "" : " Tu es en quelle classe ?");
    const college = ["6e", "5e"].includes(classe);
    const fin = ["4e", "3e"].includes(classe);
    const suite = college ? "Qu'est-ce que tu préfères là-dedans, et qu'est-ce que tu aimes faire en dehors de l'école ?"
      : fin ? "Est-ce que tu as déjà une idée de ce que tu aimerais faire après la 3e, ou d'un métier qui te tente ?"
      : "Est-ce qu'il y a des métiers ou des domaines qui te tentent, même vaguement ?";
    if (classe && gouts) return intro + `Tu es en ${classe} et tu aimes ${gouts}. ${suite}`;
    if (classe) return intro + `Tu es en ${classe}. Qu'est-ce que tu aimes faire, à l'école ou en dehors ?`;
    if (gouts) return intro + `Tu aimes ${gouts}. Tu es en quelle classe ?`;
    return intro + "Pour commencer, tu es en quelle classe, et qu'est-ce que tu aimes faire ?";
  }

  function start() {
    const vars = {
      profil: $("v-profil").value,
      classe: $("v-classe").value,
      lieu: $("v-lieu").value.trim() || "inconnu",
      interets: $("v-int").value.trim() || "inconnus",
      question: question || "aucune",
    };
    vars.accroche = accrocher(vars, question);
    const w = monterVoix($("voice-slot"), "orientation", vars, { clientTools, expanded: true });
    if (w) $("v-status").textContent = "Claire t'attend en bas à droite. Clique sur le bouton d'appel et autorise le micro, ou écris-lui.";
  }
  $("v-go").onclick = () => { question = question || ""; start(); };
  $("ideas-chips").querySelectorAll(".chip").forEach((b) => b.onclick = () => { question = b.textContent; start(); });

  if (P.scenario) { const s = $("v-scenario"); s.hidden = false; s.textContent = "Scénario de test : " + P.scenario; }
  if (P.auto === "1") start();
})();
