# DFA web POC Implementation Plan

> Execute inline with superpowers:executing-plans; user authorized setup and development.

**Goal:** dessiner et valider un DFA depuis le navigateur sous WSL.
**Architecture:** frontend React Flow indépendant de la représentation mathématique,
adaptateur FastAPI optionnel vers ExtendedDFA. Pas de modification des mixins.
**Tech Stack:** React, TypeScript, Vite, React Flow, FastAPI, pytest, Vitest.
**Spec:** ../specs/2026-11-18-dfa-web-poc.md

## Contraintes

automata-lib==9.2.0 ; aucun changement amont ; package installable sans dépendances web ;
travail dans le clone WSL sur codex/dfa-web-poc. Aucun push ni merge automatique.

## Review focus

Doublons masqués par les dictionnaires ; réponses réseau périmées ; suppression
d'états laissant des arcs orphelins ; sauvegarde corrompue ; boucles et arcs opposés.

## Tâches

- [x] API : `web/backend/{models,validation,app}.py`, dépendances backend séparées,
  `tests/web/test_api.py`. Écrire et exécuter les tests avant l'implémentation :
  DFA complet, vide, sans final, alphabet vide, epsilon, doublons, extrémités
  absentes, incomplétude, état initial, immutabilité et schéma HTTP.
- [x] Éditeur : `frontend/src/{model,geometry,App,StateNode,TransitionEdge}`.
  Tester en premier suppression avec arcs, sérialisation sans coordonnées,
  renommage, restauration, géométrie de boucles/arcs opposés. Implémenter les
  outils, historique, sélection contextuelle et sauvegarde versionnée.
- [x] Intégration : client HTTP typé avec annulation des requêtes périmées,
  erreurs localisées et messages réseau ; test HTTP réel depuis le navigateur.
- [x] Vérification : pytest complet, imports publics, mypy du backend,
  Vitest, TypeScript/build, MkDocs strict ; contrôle manuel dans le navigateur.
- [x] Documentation : ADR-0032, guide WEB_POC.md, tracker W01 avec preuves.
  Revue finale indépendante, correction des problèmes avérés.

## Journal

- 2026-11-18 : restructuration demandée et approuvée par l'utilisateur :
  `web/backend/` et `web/frontend/` à la racine. Imports, commandes et documentation
  migrés ; dépendances backend séparées du package de bibliothèque (ADR-0033).
  Réinstallation, 1422 tests Python (4 ignorés), 7 tests frontend, build frontend,
  mypy ciblé, imports publics et MkDocs strict vérifiés après déplacement.

- 2026-11-18 : clone à partir de main fabdd13 ; branche dédiée créée. Référence
  amont v9.2.0 récupérée en lecture seule. Design basé sur la maquette approuvée.
- Décision : aucune nouvelle worktree ; le clone WSL demandé assure l'isolation.
- Résultat : 1422 tests Python réussis, 4 tests vidéo ignorés (outils installés
  dans le système et non dans le venv), 7 tests frontend réussis. Build frontend,
  MkDocs strict, imports publics et mypy backend ciblé réussis.
- Revue indépendante : source de transition périmée après annulation corrigée
  par réconciliation et garde des extrémités avec test de régression ; déplacements
  clavier ajoutés à l'historique, y compris après annulation d'un déplacement.
- Régression manuelle à conserver : sélectionner un état, flèche droite, Annuler
  doit restaurer sa position ; flèche bas après Annuler doit désactiver Rétablir.
  Ajouter un état, le choisir comme départ de transition, Annuler sa création :
  le prochain clic doit choisir un nouveau départ sans créer d'arc orphelin.
- Contrôles navigateur : sauvegarde/rechargement, validation réelle, suppression
  avec arcs incidents, boucles et arcs opposés, interface 390px, aucune erreur
  console observée. Serveurs locaux laissés actifs pour essai utilisateur.
