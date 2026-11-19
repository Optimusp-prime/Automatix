# Vérification de l’éditeur web — 19 novembre 2026

## Résultats

- Suite Python : **1443 réussis, 4 ignorés**, un avertissement de dépréciation
  httpx/TestClient. Les quatre tests vidéo nécessitent des exécutables dans
  l’environnement Python ; ils étaient déjà ignorés avant ces changements.
- Frontend : **31 tests réussis**, compilation TypeScript et Vite réussie.
- Backend : mypy strict réussi sur les six fichiers.
- Documentation : compilation MkDocs stricte réussie ; imports DFA/NFA/GNFA vérifiés.

Les nouveaux tests de `tests/web/test_algorithms.py` passent par le vrai processus
de conversion et vérifient les langages, la minimisation, les cas vides, les erreurs
et les délais. `editorPresentation.test.ts` vérifie la géométrie et les métadonnées
visuelles sans reproduire seulement les fonctions de rendu.

## Parcours navigateur

Conversion de `(a|b)*abb`, aperçu isolé, remplacement et validation du DFA obtenu ;
conversion inverse avec résultat copiable et lisible à 390px. Redimensionnement
d’un état automatiquement agrandi (104 → 136 px), annulation en une étape,
déplacement et recalcul des courbes, effacement/annulation et restauration après
rechargement. Palette bleu nuit avec texte blanc vérifiée visuellement.

La revue indépendante a relevé deux problèmes corrigés : Échap dans le champ du
dialogue de transition, et l’énumération non bornée des cellules du routeur sur
des coordonnées extrêmes. Le premier a été reproduit puis vérifié dans le
navigateur ; le second est couvert par des tests de régression.

## Limites conservées

Le routage reste une recherche géométrique bornée : il peut subsister des
croisements et une congestion signalée sur les dessins denses ou les états qui
se chevauchent. Il ne promet pas une mise en page planaire. La conversion conserve
les limites de calcul documentées dans le guide. Les réglages VS Code personnels
ne font pas partie du commit de l’application.
