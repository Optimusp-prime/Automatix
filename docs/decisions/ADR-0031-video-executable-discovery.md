# ADR-0031 — Découverte locale des outils vidéo

Status: Accepted
Date: 2026-11-16

## Contexte

Un noyau de notebook peut utiliser le bon Python Conda sans avoir le dossier
`Library/bin` dans son PATH. L'export trouvait déjà FFmpeg mais Graphviz échouait,
obligeant l'utilisateur à ajouter un chemin personnel dans chaque notebook.

## Décision

Partager la découverte privée de `dot` et `ffmpeg` : PATH en priorité, puis
répertoires conventionnels relatifs à `sys.executable`. Aucun chemin utilisateur
codé en dur, aucune mutation de `os.environ` ou de la configuration globale
de graphviz. Invoquer directement l'exécutable Graphviz trouvé avec `-Tplain`,
entrée/sortie UTF-8, arguments séparés et sans shell. Le DOT reste celui du
moteur commun ; placement, composition et encodage atomique ne changent pas.

L'argument `filename` devient facultatif, avec `animation.mp4` comme défaut
relatif au dossier courant. Un dossier existant désigne `animation.mp4` dans
ce dossier. Les chemins explicites vers un MP4 gardent leur comportement et
leur type de retour Path. Aucun dossier manquant n'est créé implicitement.

## Alternatives et conséquences

Modifier globalement PATH ou `DOT_BINARY` interférerait avec le notebook et
les autres exports. Installer automatiquement des outils est hors périmètre.
Les outils absents restent des erreurs explicites. Les tests exécutent de
vrais exports avec PATH vide, contrôlent les trois formes de destination et
vérifient que l'environnement du processus est inchangé.

## Supersedes

Complète ADR-0027 et ADR-0030 pour la découverte des exécutables et la
destination facultative ; les décisions visuelles restent inchangées.
