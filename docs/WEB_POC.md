# Éditeur web DFA — POC local

Dessinez un automate déterministe, puis faites vérifier sa structure par
Automatix. Cette première version couvre le dessin et la validation des DFA
complets, ainsi que les conversions d’expressions régulières. Elle ne simule
pas encore la lecture d'un mot.

## Installation sous WSL

Depuis la racine du dépôt, avec Python 3.11+ et Node.js 22.12+ :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . -r web/backend/requirements-dev.txt
cd web/frontend
npm ci
```

L'installation Python avec `pip install -e .` permet d'utiliser uniquement
la bibliothèque. Graphviz et FFmpeg ne sont pas nécessaires pour cet éditeur.

## Lancer l'éditeur

Dans un premier terminal WSL, à la racine du dépôt :

```bash
.venv/bin/python -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000
```

Dans un second terminal WSL :

```bash
cd web/frontend
npm run dev
```

Ouvrez <http://localhost:5173> dans le navigateur Windows. Gardez les deux
terminaux ouverts ; `Ctrl+C` arrête chaque serveur. Si un port est déjà occupé,
arrêtez l'ancienne instance avant de relancer. Le serveur Vite transmet les
requêtes `/api` à FastAPI sur le port 8000.

Ces serveurs sont destinés au développement local et écoutent uniquement sur
`127.0.0.1`. Le build frontend seul n'inclut pas de serveur Python ; un déploiement
public et son hébergement restent hors du périmètre de ce POC.

## Dessiner

1. Saisissez l'alphabet dans le panneau flottant en haut à droite, par exemple
   `a, b` ou `0, 1`. Sur mobile, ce panneau occupe la première ligne.
2. Cliquez sur **Ajouter le premier état**, puis utilisez **État** et cliquez
   dans le canevas pour en ajouter d'autres.
3. Avec **Sélection**, déplacez les états. Cliquez sur un état pour changer son
   nom et ses propriétés **Initial** / **Final**. Le premier état créé est initial.
   Les propriétés apparaissent dans un panneau flottant à gauche. Tirez une
   poignée du cercle sélectionné pour le redimensionner, ou saisissez son
   **Diamètre**. Le cercle conserve ses proportions ; sa taille minimale garde
   le nom entièrement lisible. Un nom plus long agrandit automatiquement le cercle
   autour de son centre. Une manipulation se défait avec une seule annulation.
   Le diamètre minimal augmente aussi avec le nombre de flèches entrantes ou
   sortantes : à partir de trois flèches sur un côté, 20 px supplémentaires par
   flèche, avec un plafond automatique de 240 px. Une flèche portant **a, b, c**
   compte une seule fois ; une boucle compte une entrée et une sortie, et la
   flèche initiale compte une entrée. Le centre reste fixe. Une taille manuelle
   supérieure est conservée ; supprimer des transitions peut réduire la seule
   contribution automatique. Le nom reste toujours entièrement lisible.
   **Couleur de fond** ouvre un sélecteur de couleur. Le nom et le cercle intérieur
   des états finaux passent automatiquement en noir ou blanc selon le contraste.
   La couleur reste visible pendant la sélection et est sauvegardée localement,
   sans être envoyée à l’API de validation. Les anciens dessins restent blancs.
4. Avec **Transition**, cliquez sur la source, puis sur la destination et
   saisissez un symbole. Cliquez deux fois sur le même état pour une boucle.
   Vous pouvez aussi survoler un état : quatre petits points apparaissent
   uniquement dans ce mode. Maintenez un point et tirez la corde vers un état,
   puis relâchez pour saisir le symbole. Relâcher dans le vide annule le tracé.
   Relâcher sur l'état de départ permet de créer une boucle. `Échap` annule aussi
   un geste en cours. Sur écran tactile, les points restent visibles en mode Transition.
5. Cliquez sur un arc ou son étiquette pour modifier son symbole ou le supprimer.
   Les transitions ayant la même source et la même destination partagent une
   seule flèche, boucles comprises, avec une étiquette comme **a, b, c**.
   Cliquez sur le symbole voulu dans cette étiquette pour modifier ou supprimer
   uniquement sa transition. Déformer la corde ajuste la courbe du groupe entier.
   Les directions opposées restent distinctes. Les données et la validation
   conservent une transition par symbole ; le regroupement est visuel uniquement.
   Les dessins existants sont regroupés automatiquement, en utilisant la courbe
   de la première transition du groupe. La flèche initiale commence par un point.
   Le tracé cherche automatiquement à contourner les autres états et à séparer
   les lignes presque superposées, dans l’éditeur et les aperçus. Il s’adapte aux
   déplacements et aux diamètres. Les symboles cherchent une place dégagée près
   de leur courbe. Une courbe manuelle est conservée lorsqu’elle est dégagée ;
   sinon le rendu peut l’ajuster. Les positions des états ne sont pas modifiées.
   Les croisements ponctuels restent possibles. Un soulignement pointillé signale
   les tracés encore serrés ; écartez les états ou ajustez ces courbes si nécessaire.
   Supprimer un état supprime aussi ses transitions incidentes.
   Avec **Sélection**, saisissez directement la corde (hors de son étiquette)
   pour modifier sa courbure. Ses extrémités restent attachées aux états ; les
   boucles peuvent être orientées de la même façon. Une déformation correspond
   à une seule opération d'annulation. Les courbes sont sauvegardées localement,
   comme les positions, mais ne sont pas envoyées à l'API de validation.
6. Cliquez sur **Valider**. Les erreurs désignent les éléments concernés ;
   sélectionner une erreur permet de retrouver l'état ou la transition.

Les outils possèdent les raccourcis `V` (sélection), `E` (état), `T` (transition)
et `H` (main). `Échap` quitte l'action en cours ; `Suppr` retire la sélection.
`Ctrl+Z` annule et `Ctrl+Maj+Z` ou `Ctrl+Y` rétablit. Les raccourcis d'édition
restent ceux du champ de texte lorsqu'un champ est actif.

Le dessin est sauvegardé localement dans ce navigateur, après un court délai.
Les positions, diamètres et courbes sont conservés au rechargement ; l'historique d'annulation reste
limité à la session et aux 100 dernières opérations. Cette sauvegarde n'est ni
une sauvegarde serveur ni un export de fichier. Un autre navigateur ou une
autre origine possède son propre dessin. Une sauvegarde illisible est signalée
et remplacée par un document vide.

## Effacer et appliquer un algorithme

La gomme **Effacer la feuille** retire tous les états et transitions en conservant
l’alphabet. **Annuler** retrouve le dessin en une seule action.

Le bouton **Algorithmes** ouvre **Expressions régulières** :

- **Automate → expression régulière** : DFA complet valide requis ; résultat copiable.
- **Expression régulière → automate** : construit un DFA complet par dérivées.
- **Expression régulière → automate minimal** : construit le DFA puis le minimise.

L’alphabet est celui de la feuille. Syntaxe : `a|b`, `ab`, `a*`, `(a|b)*`,
`ε` ou `()` pour le mot vide et `∅` seul pour le langage vide. Le champ vide
désigne aussi le mot vide. Les opérateurs ne peuvent pas être des symboles de
l’alphabet dans ces conversions.

Un aperçu précède **Utiliser sur la feuille**, qui remplace le dessin et reste
annulable. Modifier la source retire le résultat précédent. Les états générés
sont nommés `q0`, `q1`, etc.

Limites : 120 caractères saisis, 12 états pour la conversion en expression,
15 secondes par calcul, sortie de 200 états / 4000 transitions ou 50000 caractères.
Sous WSL, chaque calcul a une limite mémoire de 512 Mio dans un processus séparé.
Relancer le serveur Python pour charger la route s’il tournait sans `--reload`.
Ces actions ont été vérifiées par les tests et dans le navigateur le 19 novembre
2026. Voir le [rapport de vérification](WEB_VERIFICATION.md) et
[ADR-0036](decisions/ADR-0036-web-regex-actions.md).

## Règles de validation du DFA

- Au moins un état, exactement un état initial ; aucun état final est autorisé.
- Noms d'états non vides et distincts ; identifiants internes stables.
- Alphabet explicite : caractères uniques, sans espace ni epsilon `ε`.
  Un alphabet vide est autorisé.
- Une transition par couple (état, symbole), vers un état existant.
  Même deux arcs identiques constituent un doublon.
  L'éditeur bloque désormais l'ajout d'un doublon et les changements de symbole
  qui en créeraient un, même vers une destination différente. Un message indique
  l'état et le symbole concernés. Les anciens dessins contenant des doublons
  sont conservés pour correction ; l'API les signale toujours lors de la validation.
- Les états inaccessibles et les états puits sont autorisés.

Un brouillon peut être incomplet ou incorrect pendant son édition. La validation
renvoie alors les erreurs, sans modifier le dessin. Les limites sont 200 états,
128 symboles, 4 000 transitions et 64 caractères par nom/identifiant. Seules les
40 premières erreurs sont affichées simultanément ; le total reste indiqué.

## API

La documentation interactive est disponible sur <http://localhost:8000/docs>.
`GET /api/health` vérifie le service. `POST /api/dfa/validate` reçoit :

```json
{
  "alphabet": ["a"],
  "states": [{"id": "q0", "label": "q0", "initial": true, "final": false}],
  "transitions": [{"id": "t0", "source": "q0", "target": "q0", "symbol": "a"}]
}
```

Une requête compatible reçoit HTTP 200 avec `valid` et `issues`. Chaque erreur
contient `code`, `message`, `state_id`, `transition_id` et `symbol` (les trois
derniers peuvent être nuls). HTTP 422 indique un schéma ou une limite de transport
non respecté. Une panne réseau est distinguée d'un DFA invalide. Les positions
visuelles ne sont pas envoyées à l'API. Toute édition invalide le résultat affiché
et annule la requête en cours ; une validation expire après 15 secondes.

L'adaptateur contrôle les listes avant conversion en dictionnaires pour ne pas
masquer les doublons, puis construit un véritable `ExtendedDFA` complet et appelle
sa validation. Aucune méthode mathématique existante n'est modifiée.

## Vérifier le développement

```bash
.venv/bin/python -m pytest
cd web/frontend
npm test
npm run build
```

Les tests Python de l'API nécessitent `web/backend/requirements-dev.txt`. Sans ces dépendances,
ils sont ignorés. Les tests frontend couvrent le modèle de dessin et la géométrie.
Ils vérifient aussi que les états et les points d'attache des transitions
conservent leurs dimensions pendant le déplacement, sans attendre le relâchement.

Au 18 novembre 2026, `npm audit --omit=dev` ne signale aucune vulnérabilité.
L'audit complet signale six entrées de sévérité haute liées à `picomatch`
(GHSA-fc5q-39xc-vjpf) dans l'outillage de développement ; aucune version corrigée
n'était disponible lors de la vérification. Recontrôler cette dépendance avant
toute ouverture du serveur de développement à d'autres machines.

Architecture : [ADR-0033](decisions/ADR-0033-root-web-application.md).
Les dimensions locales sont décrites dans [ADR-0035](decisions/ADR-0035-editor-state-size.md).
