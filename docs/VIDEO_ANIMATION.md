# Vidéo d'exécution d'un mot

`ExtendedDFA.export_animation_video()` produit une vidéo MP4 1280×720 au rendu
« Fil de lecture ». Le graphe reste fixe pendant toute la lecture.

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

Depuis la racine du dépôt, générer les trois exemples avec :

```console
python -m notebooks.video_fil_lecture --output notebooks/video_fil_lecture
```

Le lecteur HTML historique `animate()` conserve son contrat. Cette refonte porte
sur l'export vidéo. Architecture : [ADR-0030](decisions/ADR-0030-fil-de-lecture-video.md).
