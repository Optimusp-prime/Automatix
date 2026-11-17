# Travaux restants pour la couverture du TD

Dernière mise à jour : 2026-11-12.

Cette liste conserve les tâches convenues après l'audit des 74 exercices
de `Enonce_TD.v04.pdf`. Elle complète les exigences #1–#62 et les ajouts
déjà vérifiés ; elle ne signifie pas que ces fonctionnalités sont toutes
obligatoires pour la remise du projet.

Tous les éléments ci-dessous sont **TODO**. Les noms d'API restent à
définir lors de la conception, après vérification des primitives existantes.

## Prochaine étape

Commencer par B01 (tables de transitions), puis B02 (calculs pas à pas).
Traiter chaque fonctionnalité séparément avec conception, tests,
documentation et mise à jour du suivi avant de passer à la suivante.

## Fonctionnalités à développer

| ID | Ordre conseillé | Tâche | Exercices | Résultat attendu et limites |
| --- | --- | --- | --- | --- |
| B01 | 1 | Tables de transitions | 14, 33, 36, 41–42 | Afficher ou exporter les transitions avec état initial, états finaux, destinations multiples et ε. Ne pas confondre avec la table de distinguabilité déjà disponible. |
| B02 | 2 | Calculs pédagogiques pas à pas | 31–33, 41–42, 50 | Exposer les étapes de déterminisation, élimination ε, partitions de minimisation, substitutions d'Arden et élimination d'états. Réutiliser les moteurs actuels ; certaines informations sont déjà accessibles (rounds des paires, classes finales, sous-ensembles, équations). |
| B03 | 3 | Recherche dans un espace d'états implicite | 71, 74.5 | Générer les successeurs à la demande, détecter un objectif et reconstruire une plus courte suite d'actions. Définir les limites d'exploration pour un espace potentiellement infini. Un plus court mot accepté sur un automate explicite est déjà calculable. |
| B04 | 4 | Composition de systèmes à actions communes et privées | 70.3 | Synchroniser les actions communes et laisser évoluer indépendamment les actions privées. Distinguer le produit totalement synchronisé et l'entrelacement déjà disponibles. |
| B05 | 5 | Simplification algébrique des regex | 46 | Aller au-delà des identités simples et de la normalisation interne actuelle ; restituer les réécritures. Définir les règles et critères, sans promettre une expression globalement minimale. |
| B06 | 6 | Constante d'itération minimale | 58–59 | Définir précisément la convention du lemme, puis calculer une valeur minimale. Une borne issue du nombre d'états n'est pas automatiquement minimale. Conception mathématique préalable nécessaire. |
| B07 | 7 | Grammaires générales | 53–54, 56 | Étendre au-delà des productions régulières à droite : définir les productions, terminaux, dérivations et opérations réellement prises en charge. Ne pas promettre la conversion de toute grammaire en automate fini. |
| B08 | À clarifier | Insertion d'un symbole à une position quelconque | 39.4 | Clarifier d'abord l'énoncé : sa formule décrit L·{s}·L, déjà composable, tandis que sa phrase décrit une insertion dans un mot de L. Implémenter seulement la transformation retenue. |

## Interfaces pratiques réutilisant les fonctions existantes

| ID | Tâche | Portée à cadrer |
| --- | --- | --- |
| B09 | Observateur et prédicat d'opacité | Ex. 73 : réutiliser les sous-ensembles accessibles de la déterminisation et tester si une observation impose un état secret. Préciser les événements invisibles et la définition d'opacité. |
| B10 | Prédicat de langage suffixe-clos | Réutiliser miroir → déterminisation → test préfixe-clos. |
| B11 | Complétude relative et changement d'alphabet | Ex. 26.2, 13.2, 19.3 : encapsuler les requêtes/reconstructions déjà possibles, avec validation des alphabets. |
| B12 | Opérations directes sur les grammaires régulières | Ex. 55 : union, concaténation et étoile ; le détour par les automates fonctionne déjà. |
| B13 | Blocages et terminaison | Ex. 70.5, 72.7 : réutiliser accessibilité, voisinage, cycles et SCC. Définir arrêt, objectifs, exécutions maximales et éventuelles hypothèses d'équité ; distinguer ces propriétés de la finitude du langage accepté. |

Ces interfaces constituent principalement des améliorations d'usage et
de tests métier, pas nécessairement de nouveaux algorithmes.

## Exemples et contenu pédagogique

| ID | Tâche | Portée |
| --- | --- | --- |
| B14 | Modèles applicatifs et démonstrations testées | Ex. 68–74 : code d'accès, tennis, café, berger/loup/chèvre/chou, planète, opacité et récipients. Séparer les modèles des primitives génériques. |
| B15 | Définitions et preuves mathématiques | Ex. 1–12, 17–18, 23–25, 45, 48–49 et 60–67 : définitions, induction, correction, lois de fermeture et non-régularité. Il s'agit de contenu pédagogique, sans engagement à créer un démonstrateur automatique général. |
| B16 | Actualiser la documentation de référence et les exemples | Signaler les anciens exemples incorrects sur `from_grammar_string` et `eliminate_lambda`, déjà corrigés dans Automatix ; actualiser les chiffres du README et documenter les compositions disponibles. |

## Déjà terminé : ne pas réimplémenter

- TD38 : `ExtendedNFA.accepting_runs()` et `count_accepting_runs()` pour
  NFA sans ε, avec 47 tests dédiés. Voir [documentation](ACCEPTING_RUNS.md).
- TD51 : `Regex.to_dfa()` par dérivées normalisées, avec 32 tests dédiés.
  Voir [documentation](DERIVATIVE_DFA.md).
- Produit à la volée, quotients par mot, élimination ε et alias
  `eliminate_lambda()` : disponibles.
- Duplication de la dernière lettre et L·{s}·L : réalisables par composition.
- Le comptage avec transitions ε et cycles potentiellement infinis reste
  hors du contrat TD38 actuel ; toute extension demandera une conception
  séparée, sans élimination ε implicite.

Le suivi canonique reste [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).
La vérification du 2026-11-12 avant commit a donné **1 381 tests réussis,
aucun ignoré**, et un typage strict validé sur **121 fichiers**.
