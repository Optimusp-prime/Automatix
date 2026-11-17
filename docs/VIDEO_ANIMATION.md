# Vidéo d'exécution d'un mot

`ExtendedDFA.export_animation_video()` produit une vidéo MP4 1280×720 au rendu
« Fil de lecture ». Le graphe reste fixe pendant toute la lecture.

Une fois l'automate créé, aucun `import os` ni ajout au `PATH` n'est nécessaire
si Graphviz et FFmpeg sont installés dans l'environnement Python utilisé :

```python
A.export_animation_video("101010")  # animation.mp4 dans le dossier courant
A.export_animation_video("101010", "ma_video.mp4")
A.export_animation_video("101010", "videos")  # dossier existant : videos/animation.mp4
```

Le dossier courant est celui du noyau du notebook ou du processus Python.
Un chemin absolu peut également être fourni. Les dossiers ne sont pas créés
automatiquement ; un fichier existant est remplacé après un export réussi.

Pour choisir l'environnement contenant Graphviz et FFmpeg :

```python
A.export_animation_video("101010", env_path=r"C:\mes_envs\automate")
A.export_animation_video("101010", "ma_video.mp4", env_path="./.venv")
```

`env_path=None` (valeur par défaut) conserve la découverte automatique actuelle.
Le chemin fourni est la **racine du dossier d'environnement**, pas `python.exe`
ni `Library/bin`. Les chemins relatifs et `~` sont acceptés. Avec un chemin
explicite, les deux outils doivent être présents dans cet environnement ; aucun
autre environnement n'est utilisé en remplacement. Cette option choisit les
exécutables externes, sans changer le noyau Python du notebook ni son `PATH`.

```python
from automata_extensions.fa import ExtendedDFA

automate = ExtendedDFA(
    states={1, 2, 3, 4, 5},
    input_symbols={"0", "1"},
    transitions={1: {"1": 2}, 2: {"0": 5, "1": 3}, 3: {},
                 4: {"0": 5}, 5: {"0": 3, "1": 4}},
    initial_state=1, final_states={1, 5}, allow_partial=True,
)
automate.export_animation_video("101010", "accepte.mp4", fps=0.8)
automate.export_animation_video("10100", "refuse.mp4", fps=0.8)
automate.export_animation_video("110101", "transition_absente.mp4", fps=0.8)
```

## Lecture du rendu

- Mot en haut à gauche, sans titre ni légende superflue.
- Symboles consommés estompés à 25 % ; légère pulsation à la consommation.
- Tracé progressif de la transition, départ et arrivée en douceur, fondu entre
  états et halo léger. Doubles cercles et flèche initiale conservent leur sens.
  Les pointes s'arrêtent à environ deux pixels du contour extérieur de l'état
  d'arrivée, y compris pour la flèche initiale et les boucles.
- Verdict final **Accepté** ou **Refusé**, avec coche/croix.
- Transition absente : symbole bloquant et suffixe non lu à 100 % d'opacité,
  traits inférieurs rouges ; arrêt au dernier état réel, sans état puits ajouté.
- Mot entièrement lu mais état non final : seul le dernier symbole reçoit le
  repère rouge à 100 %. C'est un repère de refus du mot, pas une transition invalide.
- Mot vide : ε puis verdict. Les mots longs utilisent une fenêtre de 18 symboles
  et des points de suspension ; le suffixe hors champ reste non consommé.

`fps` est le nombre de symboles par seconde (`0.8` donne 1,25 seconde par symbole).
`render_fps`, 30 par défaut, est la cadence vidéo. Si la lecture est plus rapide
que la cadence vidéo, les états restent corrects mais les mouvements intermédiaires
ne peuvent pas tous être représentés.

## Prérequis et exemples

Graphviz (`dot`) et FFmpeg sont nécessaires à l'export ; Pillow est une dépendance
Python du projet. Le répertoire de destination doit exister. L'automate n'est pas
modifié, et un fichier existant n'est remplacé qu'après un encodage réussi.
Les exécutables sont recherchés sur le `PATH`, puis à côté du Python courant
(y compris `Scripts` et `Library/bin` sous Windows/Conda, ou `bin` sous Linux/macOS).
Aucun chemin propre
à une machine n'est inscrit dans le code, et le `PATH` du processus n'est pas
modifié. Si un outil est réellement absent, l'export indique lequel installer.

Depuis la racine du dépôt, générer les trois exemples avec :

```console
python -m notebooks.video_fil_lecture --output notebooks/video_fil_lecture
```

Le lecteur HTML historique `animate()` conserve son contrat. Cette refonte porte
sur l'export vidéo. Architecture : [ADR-0030](decisions/ADR-0030-fil-de-lecture-video.md).
