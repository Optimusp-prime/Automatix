# Bienvenue dans Automatix

![Illustration d'un mot binaire entrant dans un réseau d'états reliés par des transitions, jusqu'à un état final à double cercle.](assets/automatix-hero-illustration.png){: .intro-hero }

Comprendre les automates, les construire en Python et voir les mots prendre
vie, symbole après symbole.
{: .intro }

Automatix est un projet pédagogique réalisé dans le cadre d'un travail
confié par **M. Kagny François, mon professeur**. Il relie les notions du
cours de langages formels à des expériences concrètes : créer un automate,
tester un mot, observer son exécution et comprendre le résultat.

La bibliothèque étend **automata-lib 9.2.0** avec des outils pour les
automates, les expressions régulières et les grammaires régulières.
Vous pouvez commencer avec l'exemple ci-dessous, puis explorer les guides
à votre rythme.

<ul class="learning-path">
  <li><strong>1. Comprendre</strong>Un état décrit où l'on se trouve ; une transition indique où aller en lisant un symbole.</li>
  <li><strong>2. Expérimenter</strong>Construisez un petit automate et comparez des mots acceptés et refusés.</li>
  <li><strong>3. Observer</strong>Animez une exécution pour suivre chaque symbole et chaque transition.</li>
</ul>

## Un automate, comment ça marche ?

Un automate lit un **mot**, c'est-à-dire une suite de symboles d'un
**alphabet**. Il part d'un **état initial** et suit les transitions au fil
de la lecture. Dans un automate déterministe, chaque symbole détermine au
plus une transition depuis l'état courant.

Le mot est **accepté** si la lecture se termine dans un **état final**.
Il est **refusé** si une transition nécessaire manque ou si l'état atteint
après le dernier symbole n'est pas final.

Prenons un exemple simple : reconnaître `a`, `aa`, `aaa`, etc., mais
refuser le mot vide. L'alphabet contient uniquement le symbole `a`.

## Installer la bibliothèque

Avec **Python 3.11 ou plus**, ouvrez un terminal dans le dossier du projet :

```bash
python -m pip install -e .
```

Vous pouvez ensuite exécuter les exemples dans un script Python ou dans
un notebook utilisant cet environnement.

## Construire votre premier automate

```python
from automata_extensions.fa import ExtendedDFA

dfa = ExtendedDFA(
    states={"q0", "q1"},
    input_symbols={"a"},
    transitions={
        "q0": {"a": "q1"},
        "q1": {"a": "q1"},
    },
    initial_state="q0",
    final_states={"q1"},
)
```

Au départ, on se trouve dans `q0`, qui n'est pas final. Le premier `a`
mène à `q1`, un état final. Chaque `a` suivant nous laisse dans `q1`.
L'automate reconnaît donc exactement les mots contenant **au moins un `a`**
sur cet alphabet.

## Tester et comprendre le résultat

```python
print(dfa.accepts("a"))    # True
print(dfa.accepts("aaa"))  # True
print(dfa.accepts(""))     # False : aucun symbole n'a été lu
```

Pour `aaa`, le parcours est `q0 → q1 → q1 → q1`. Tous les symboles ont
été lus et l'état d'arrivée est final : le mot est accepté.
Pour le mot vide, noté **ε** en mathématiques et `""` en Python, on reste
dans `q0` : le mot est refusé.

**À vous de jouer :** avant de lancer `dfa.accepts("aa")`, prédisez le
résultat et retracez les états visités. Puis essayez le mot vide après
avoir construit un nouvel automate où `q0` est aussi final.

## Voir l'exécution en vidéo

Dans la même session Python, vous pouvez exporter la lecture de `aaa` :

```python
dfa.export_animation_video("aaa")
```

La vidéo est enregistrée dans `animation.mp4`, dans le dossier courant.
Cet export nécessite **Graphviz** et **FFmpeg** : Automatix les cherche
automatiquement dans le `PATH`, puis dans l'environnement Python courant.
Le [guide vidéo](VIDEO_ANIMATION.md) explique l'installation des outils,
le choix du fichier de sortie et l'utilisation d'un autre environnement.

## Pour aller plus loin

| Votre prochaine étape | La ressource |
| --- | --- |
| Suivre les symboles consommés et comprendre un refus | [Vidéo d'exécution](VIDEO_ANIMATION.md) |
| Explorer les différents parcours d'un automate non déterministe | [Exécutions acceptantes des NFA](ACCEPTING_RUNS.md) |
| Passer d'une expression régulière à un automate | [Automate par dérivées de regex](DERIVATIVE_DFA.md) |
| Trouver une méthode et connaître ses limites | [API et suivi des fonctionnalités](IMPLEMENTATION_STATUS.md) |
| Comprendre les choix de conception | [Décisions d'architecture](decisions/README.md) |

Les transformations comme `trim()` ou `minimize()` créent de nouveaux
automates sans modifier l'original : vous pouvez ainsi comparer les
résultats et enchaîner les opérations. Le
[recueil d'exemples](EXAMPLES.md)
propose d'autres démonstrations pour poursuivre l'exploration.
