# ÉDUCATION : un tuteur IA pour l'Éducation nationale

_Adrien Joly – Octobre 2026_

## En bref

- **Le constat.** Les familles aisées paient des cours particuliers et s'appuient sur leur réseau pour l'orientation. Un tuteur IA bien conçu peut offrir une partie de cet accompagnement à tous : les tuteurs structurés, qui guident sans donner la réponse, font gagner 0,3 à 0,6 écart-type (De Simone et al., 2025 ; Henkel et al., 2024 ; Kestin et al., 2025). Un accès libre à l'IA fait au contraire baisser les résultats aux examens sans aide de 17 à 24 % (Bastani et al., 2025 ; Strömberg, Lei et Wu, 2026).
- **La proposition.** Un tuteur public, vocal et en français, commandé par l'Éducation nationale, avec des garde-fous stricts, testé par un essai randomisé avant toute généralisation.

## 1. Ce que fait le tuteur

- **Trois usages.** L'élève se fait **interroger** (une question à la fois, des indices avant la réponse), demande une **explication** (une notion, un exemple, une question pour vérifier), ou **révise avec un binôme** qui lui fait expliquer la leçon avec ses mots. Se tester fixe mieux une notion que la relire (Roediger et Karpicke, 2006).
- **La voix d'abord.** À l'oral, l'élève est actif et n'a pas besoin de bien lire. Le prototype propose trois professeurs pour le brevet : histoire-géographie (les repères à connaître par cœur), mathématiques (calcul mental) et français (grammaire, récitation, oral du brevet). Un professeur peut y mettre sa propre voix clonée, avec son accord écrit. Le tuteur parle français et passe à l'anglais en cours de conversation si l'élève ou un parent le demande. Le seul outil vocal acheté par l'État, Mathia (P2IA, cycle 2), n'a jamais été évalué publiquement.
- **Un volet orientation, de la 6e à la terminale.** La guide propose options, stages, concours, mentors et formations selon l'âge, les goûts et le lieu de vie de l'élève. Elle s'appuie sur la note de résilience à l'IA des 13 819 formations de Parcoursup 2025, leurs salaires, leurs taux d'emploi à 30 mois (InserSup) et leurs taux d'accès.

## 2. Des garde-fous stricts

- **Jamais les devoirs à la place de l'élève.** Le tuteur refuse d'écrire une rédaction ou de donner le résultat d'un exercice : il le fait faire étape par étape. Un second modèle relit chaque réponse et bloque celles qui feraient le travail. C'est la conception qui supprime presque tout l'effet négatif mesuré par Bastani et al. (2025). Le cadre d'usage de 2025 qualifie déjà de fraude un devoir rédigé par IA sans autorisation.
- **Protéger les mineurs.** Ni nom, ni adresse, ni établissement ; pas de sujet hors école ; en cas de détresse, renvoi vers un adulte et les numéros 3020, 3018, 119 et 3114 ; hébergement des données en France.

## 3. Une commande publique qui reste à jour

- **Éviter l'erreur de MIA Seconde** : commandé en 2022 pour 2,8 M€ sur trois ans, livré avec un an de retard, sans résultats publiés (Next, 2024). Séparer quatre lots : pédagogie et garde-fous ; accès aux modèles par une passerelle publique (l'API Albert de la DINUM en fait déjà fonctionner plusieurs) ; voix, avec des modèles français ouverts (Kyutai, Mistral) ; données d'orientation (Onisep, Parcoursup).
- **Un contrat exigeant.** Passer à un meilleur modèle en trois mois au plus, remettre le modèle en concurrence tous les 12 à 24 mois, et lier 20 à 30 % du paiement aux résultats d'un essai indépendant, mesurés sur des épreuves sans l'outil.
- **Un essai d'abord.** Démarrer dans quelques académies, avec un groupe témoin. Ouvrir le tuteur dès la 6e va au-delà du cadre de 2025, qui réserve l'usage par l'élève à partir de la 4e : l'essai doit le justifier.

* Pour essayer : la [Boussole IA des formations](https://ajoly35.github.io/tuteur-ia/boussole/), qui classe les formations de Parcoursup selon leur résilience à l'IA. Le prototype vocal : [le tuteur de révision](https://ajoly35.github.io/tuteur-ia/tuteur/) (histoire-géographie, mathématiques et français) et [la guide d'orientation](https://ajoly35.github.io/tuteur-ia/orientation/). Scénarios de test : [interrogation sur la guerre froide](https://ajoly35.github.io/tuteur-ia/tuteur/?prof=histoire&mode=interroger&sujet=la%20guerre%20froide%20%281947-1991%29&auto=1) ; [répétition de l'oral du brevet](https://ajoly35.github.io/tuteur-ia/tuteur/?prof=francais&mode=binome&sujet=pr%C3%A9parer%20l%27oral%20du%20brevet&auto=1) ; [Claire conseille un élève de 3e à Vire](https://ajoly35.github.io/tuteur-ia/orientation/?profil=%C3%A9l%C3%A8ve&classe=3e&lieu=Vire%2C%20Calvados&interets=la%20m%C3%A9canique%20et%20le%20sport&question=Voie%20pro%20ou%20seconde%20g%C3%A9n%C3%A9rale%20%3F&auto=1&scenario=%C3%89l%C3%A8ve%20de%203e%20%C3%A0%20Vire%2C%20h%C3%A9site%20entre%20voie%20pro%20et%20seconde%20g%C3%A9n%C3%A9rale.%20Dites%20que%20le%20conseil%20de%20classe%20vous%20pousse%20vers%20la%20voie%20pro.) ; [Claire répond à un parent de Guéret](https://ajoly35.github.io/tuteur-ia/orientation/?profil=parent&classe=4e&lieu=Gu%C3%A9ret%2C%20Creuse&question=On%20n%27a%20pas%20de%20r%C3%A9seau%2C%20comment%20aider%20notre%20fils%20%3F&auto=1&scenario=Parent%20d%27un%20%C3%A9l%C3%A8ve%20de%204e%20%C3%A0%20Gu%C3%A9ret%2C%20sans%20r%C3%A9seau.) ; [tous les scénarios](https://ajoly35.github.io/tuteur-ia/tests.html). Il faut un micro et accepter son usage dans le navigateur.

### Références

Bastani et al. (2025), PNAS ; De Simone et al. (2025), Banque mondiale PRWP 11125 ; Henkel et al. (2024), arXiv 2402.09809 ; Kestin et al. (2025), Scientific Reports ; Strömberg, Lei et Wu (2026), CEPR DP21577 ; Roediger et Karpicke (2006), Psychological Science ; Next (2024), MIA Seconde ; DINUM (2026), API Albert ; MENJ (2025), Cadre d'usage de l'IA en éducation ; MESR-SIES (2026), InserSup ; Hosseini et Lichtinger (2026).
