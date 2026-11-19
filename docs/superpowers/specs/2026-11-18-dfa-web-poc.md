# POC web DFA — design convenu

## Demande et périmètre

L'utilisateur a validé une première maquette, puis autorisé le setup et le
développement sous WSL Ubuntu-24.04. Il demande un éditeur sobre, inspiré de
Figma/Excalidraw : états circulaires, transitions orientées, alphabet explicite,
validation à la demande. DFA complets uniquement, sans simulation de mots,
export vidéo, compte, base de données ni publication du POC.

Créer/déplacer/renommer/supprimer les états, désigner un état initial et des
états finaux (éventuellement aucun), créer/modifier/supprimer les transitions,
boucles et arcs opposés lisibles, zoom/panoramique, annuler/rétablir. Le brouillon
peut être invalide ; les erreurs de validation pointent les objets concernés.
Sauvegarde locale versionnée et restauration après rechargement.

## Architecture et contrats

- React + TypeScript + Vite + React Flow, CSS dédié ; aucune dépendance aux
  fichiers de la maquette. Frontend dans `web/frontend/`.
- FastAPI optionnel dans `web/backend/`, installé via `web/backend/requirements.txt`.
- `POST /api/dfa/validate` reçoit `{alphabet, states, transitions}`. Un état
  contient `id`, `label`, `initial`, `final`; une transition contient `id`,
  `source`, `target`, `symbol`. Aucun code Python ni coordonnées n'est envoyé.
- HTTP 200 : `{valid, issues}`; chaque problème a un code, un message français
  et, si possible, `state_id`, `transition_id`, `symbol`. HTTP 422 pour un JSON
  incompatible avec le schéma. Une panne réseau est distincte d'un DFA invalide.
- Les symboles sont des caractères Unicode uniques, non blancs, autres que ε,
  séparés par des virgules dans l'éditeur. Alphabet vide autorisé. Les noms sont
  non vides et distincts ; les identifiants techniques ne changent pas au renommage.
- Enveloppe POC : 200 états, 128 symboles, 4 000 transitions, identifiants/noms
  de 64 caractères maximum. Ces bornes sont explicites dans l'API et l'interface.
- Le serveur vérifie les doublons avant de construire les dictionnaires. Il
  construit `ExtendedDFA(..., allow_partial=False)` et appelle `validate()`.
  Les messages groupés complètent ce contrôle sans remplacer la validation amont.
- Les données d'édition sont séparées du DFA immuable. Déplacer un état n'appelle
  pas le serveur. Tout changement sémantique invalide une réponse précédente.
- API et Vite écoutent sur loopback ; proxy `/api` en développement. Aucun CORS
  permissif. Ce serveur local n'est pas une configuration de production publique.

## Sources et vérification

La demande utilisateur est un complément W01, pas une nouvelle exigence du
professeur. Le document mature du professeur n'est pas disponible. Référence
amont inspectée : tag v9.2.0, `DFA.__init__`, `DFA.validate` et
`Automaton.__post_init__`. Aucune méthode publique d'automate n'est ajoutée.
Graphviz conserve son rôle dans les exports existants ; React Flow est l'éditeur
interactif de ce consommateur web. Aucun code amont n'est modifié.

Validation : tests HTTP des cas valides/invalides, tests des transformations
du brouillon, vérification TypeScript/build, tests existants Python, contrôle
navigateur de création, édition, validation, déplacement et recharge.
