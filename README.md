# Tuteur IA public : révision vocale et orientation

Deux prototypes vocaux en français, construits pour la note « Un tuteur IA pour l'Éducation nationale » (Préparer l'avenir, GT Éducation, octobre 2026).

| Prototype | Page | Agent(s) ElevenLabs |
|---|---|---|
| **Tuteur de révision** (3e, brevet) : trois professeurs, trois façons de travailler (m'interroger, m'expliquer, réviser ensemble), garde-fous anti-devoirs, voix du professeur possible | `site/tuteur/` | Madame Lambert (histoire-géo-EMC), Monsieur Diallo (maths), Madame Morel (français) |
| **Boussole d'orientation** (6e à terminale, élèves et parents) : la Boussole IA des formations + une guide vocale qui ouvre les fiches et cherche des formations Parcoursup près de chez l'élève | `site/orientation/` | Claire |
| Dix scénarios de test | `site/tests.html` | |

## Arborescence

```
agents/
  agents.json            configuration des 4 agents (voix, premier message, variables, outils, garde-fous)
  prompts/               prompts sources : _socle-tuteur.md (commun) + un fichier par personnage
  kb/                    bases de connaissances (programmes de 3e, orientation) + SOURCES.md
  build/                 prompts assemblés (tools/build_prompts.py)
  created.json           identifiants des agents créés (écrit par tools/create_agents.py)
site/                    site statique servi par GitHub Pages
  assets/voix.js         chargeur du widget ElevenLabs + identifiants des agents
  assets/orientation-voix.js  outils côté navigateur de la guide (afficher_famille, chercher_formations, classement_familles)
  orientation/data.js    données de la Boussole (Parcoursup 2025, InserSup, Hosseini et Lichtinger 2026)
note/                    note d'une page (.md source, .docx, .pdf au format v12)
tools/                   build_prompts.py, create_agents.py, port_boussole.py
```

## Créer ou mettre à jour les agents (compte personnel)

```
ELEVENLABS_API_KEY=sk_... python3 tools/create_agents.py
```
Le script crée les documents de connaissances, les outils de la guide et les quatre agents, puis écrit leurs identifiants dans `site/assets/voix.js`. Relancé, il met à jour les agents existants. Pousser ensuite `site/` pour mettre le site à jour.

## Garde-fous

- Dans le prompt : refus de faire les devoirs (rédaction, développement construit, résultat d'exercice), méthode pas à pas, aucune donnée personnelle, numéros d'aide (3020, 3018, 119, 3114).
- Dans la plateforme : un garde-fou personnalisé relit chaque réponse et la bloque si elle fait le travail de l'élève (relance avec un message de refus bienveillant), modération (contenus sexuels, mineurs, automutilation, haine, violence), focus et protection contre l'injection de prompt.

## La voix du professeur

Un professeur clone sa propre voix dans ElevenLabs (Instant Voice Clone, une à deux minutes d'audio, avec son accord écrit), puis colle l'identifiant de voix dans la page du tuteur : le lien de classe produit (`?prof=histoire&voix=ID`) fait parler le tuteur avec sa voix. Les agents tuteurs autorisent ce remplacement de voix ; la guide d'orientation, non.

## Données et sources

- Boussole : données et méthode dans le dépôt `horizons-education-ia` (`site/build_data.py`, `data/raw/`). Note A à E = 50 % part des tâches automatisables des premiers métiers (Hosseini et Lichtinger, 2026), 25 % type de métier (Garicano), 25 % maths × contact humain (Deming, 2017).
- Programmes et orientation : `agents/kb/SOURCES.md`.

Prototype de démonstration : les agents peuvent se tromper. Ne pas utiliser avec de vrais élèves sans essai encadré.
