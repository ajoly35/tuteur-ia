"""Port the claude.ai Boussole artifact to a standalone GitHub Pages page with the ElevenLabs voice guide.

Usage: python3 tools/port_boussole.py ../note-organisation-ecole/site/boussole-ia-formations.html site/orientation/index.html
The written-chat section (window.claude sampling, unavailable outside claude.ai) is replaced by the voice guide;
the voice logic lives in site/assets/orientation-voix.js.
"""
import sys

VOICE_SECTION = '''<section class="card ask" aria-labelledby="h-ask">
    <h2 id="h-ask">Parle à Claire, ta guide d'orientation</h2>
    <p class="small">De la 6e à la terminale, pour les élèves et leurs parents. Dis-lui ce que tu aimes, où tu habites et ce que tu fais en dehors des cours : elle te propose des pistes, des formations près de chez toi, des stages, des concours et des mentors. Elle peut ouvrir les fiches de cette page pendant que vous parlez.</p>
    <div class="vgrid">
      <div class="vfield"><label for="v-profil">Je suis</label><select id="v-profil"><option value="élève">un ou une élève</option><option value="parent">un parent</option></select></div>
      <div class="vfield"><label for="v-classe">Classe</label><select id="v-classe"><option value="inconnue">je le dirai à l'oral</option><option>6e</option><option>5e</option><option>4e</option><option>3e</option><option>seconde</option><option>première</option><option>terminale</option></select></div>
      <div class="vfield"><label for="v-lieu">J'habite (ville ou département)</label><input id="v-lieu" type="text" autocomplete="off" placeholder="Par exemple : Vire, Calvados"></div>
      <div class="vfield"><label for="v-int">Ce que j'aime (facultatif)</label><input id="v-int" type="text" autocomplete="off" placeholder="Par exemple : les maths, le foot, aider les gens"></div>
    </div>
    <div class="ask-row"><button class="btn" type="button" id="v-go">Parler à Claire</button></div>
    <div class="chips" id="ideas-chips">
      <button class="chip" type="button">Quelles spécialités choisir en seconde ?</button>
      <button class="chip" type="button">Je n'ai pas de réseau pour trouver un stage</button>
      <button class="chip" type="button">L'informatique, est-ce encore une bonne idée avec l'IA ?</button>
      <button class="chip" type="button">Voie pro ou seconde générale ?</button>
    </div>
    <p class="small" id="v-status" aria-live="polite"></p>
    <div class="scenario" id="v-scenario" hidden></div>
  </section>'''

EXTRA_CSS = '''
/* Voice guide form */
.vgrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
@media (max-width: 640px) { .vgrid { grid-template-columns: minmax(0, 1fr); } }
.vfield { display: grid; gap: 4px; min-width: 0; }
.vfield label { font-weight: 700; font-size: 14px; }
.vfield input, .vfield select { width: 100%; min-width: 0; padding: 11px 12px; border-radius: 10px; border: 1px solid var(--rule); background: var(--bg); }
.scenario { padding: 12px 14px; border-radius: 10px; background: var(--accent-soft); font-size: 15px; }
.fam.flash { box-shadow: 0 0 0 3px var(--accent); }
</style>'''


def main(src_path, out_path):
    src = open(src_path, encoding="utf-8").read()
    i = src.index('<div class="wrap">')
    head, body = src[:i], src[i:]
    head = head.replace("<title>Boussole IA des formations</title>", "")
    head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    head = head.replace("</style>", EXTRA_CSS, 1)

    a = body.index('<section class="card ask"')
    b = body.index("</section>", a) + len("</section>")
    body = body[:a] + VOICE_SECTION + body[b:]

    body = body.replace("<h1>Quelles études pour un monde avec l'IA ?</h1>",
                        "<h1>Choisir son chemin, de la 6e au bac, dans un monde avec l'IA</h1>")
    body = body.replace(
        "combien on y gagne et où les suivre.</p>",
        "combien on y gagne et où les suivre. Et tu peux préparer ton parcours à voix haute, dès le collège, avec une guide d'orientation.</p>", 1)

    js_a = body.index("// ---------- Ask ----------")
    js_b = body.index("</script>", js_a)
    body = body[:js_a] + body[js_b:]
    # The voice scripts use globals of the page script ($, D, findOffers...), so they go after the last script.
    k = body.rindex("</script>") + len("</script>")
    body = body[:k] + '\n<div id="voice-slot"></div>\n<script src="../assets/voix.js"></script>\n<script src="../assets/orientation-voix.js"></script>' + body[k:]
    body = body.replace("</div>\n\n<script", '''  <footer class="small" style="border-top:1px solid var(--rule);padding-top:16px">Prototype Préparer l'avenir. Voix et conversation : ElevenLabs. <a href="../">Accueil</a> · <a href="../tuteur/">Le tuteur de révision</a> · <a href="../tests.html">Liens de test</a></footer>
</div>

<script''', 1)

    page = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<title>Boussole des formations</title>\n'
            '<meta name="description" content="Guide d\'orientation vocal de la 6e à la terminale, avec la note IA de 13 819 formations Parcoursup.">\n'
            + head.strip() + "\n</head>\n<body>\n" + body.rstrip() + "\n</body>\n</html>\n")
    open(out_path, "w", encoding="utf-8").write(page)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
