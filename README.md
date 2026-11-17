# Automatix

Bibliothèque Python pédagogique pour construire, analyser et transformer des automates finis.

[Documentation](https://optimusp-prime.github.io/Automatix/) · [Exemples](docs/EXAMPLES.md) · [État des fonctionnalités](docs/IMPLEMENTATION_STATUS.md)

Automatix est un projet académique confié par **M. Kagny François**. Il met en pratique les notions de théorie des automates et des langages formels en étendant [automata-lib](https://github.com/caleb531/automata), dans sa version **9.2.0**.

Le projet expose notamment `ExtendedDFA`, `ExtendedNFA` et `ExtendedGNFA`. Les transformations produisent de nouveaux automates sans modifier l’objet d’origine, afin de pouvoir comparer les résultats et enchaîner les opérations.

## Installation

**Python 3.11 ou plus** est requis. Depuis un terminal :

```bash
git clone https://github.com/Optimusp-prime/Automatix.git
cd Automatix
python -m pip install -e .
```

Cette installation inclut les dépendances Python, dont `automata-lib==9.2.0`. Dans un notebook, sélectionnez le noyau correspondant à l’environnement où le projet est installé.

Certains rendus nécessitent aussi des programmes externes :

| Usage | Prérequis supplémentaire |
| --- | --- |
| Calculs et exports texte DOT, TikZ ou LaTeX | Aucun |
| Rendus SVG, PNG et PDF | Graphviz (`dot` accessible dans le `PATH`) |
| Export vidéo MP4 | Graphviz et FFmpeg |

Pour la vidéo, les exécutables sont recherchés dans le `PATH`, puis dans l’environnement Python courant. Le [guide vidéo](https://optimusp-prime.github.io/Automatix/VIDEO_ANIMATION/) détaille la configuration et l’option `env_path`.

## Premier exemple

Cet automate reconnaît les mots composés d’au moins un `a`, sur l’alphabet `{a}`. Le mot vide est refusé.

```python
from automata_extensions.fa import ExtendedDFA

automate = ExtendedDFA(
    states={"q0", "q1"},
    input_symbols={"a"},
    transitions={
        "q0": {"a": "q1"},
        "q1": {"a": "q1"},
    },
    initial_state="q0",
    final_states={"q1"},
)

print(automate.accepts("aaa"))          # True
print(automate.accepts(""))             # False
print(automate.execution_trace("aa"))   # ['q0', 'q1', 'q1']

minimal = automate.trim().minimize()
print(minimal.is_equivalent(automate))  # True
```

Avec Graphviz et FFmpeg installés, exportez ensuite une animation de la lecture :

```python
automate.export_animation_video("aaa", "animation.mp4")
```

Le fichier est créé dans le dossier courant. Sans second argument, son nom est également `animation.mp4`.

## Fonctionnalités

| Domaine | Opérations proposées |
| --- | --- |
| Analyse des automates | Parcours, accessibilité, états utiles, cycles, composantes fortement connexes |
| Transformations | Élagage, complétion, minimisation, déterminisation, élimination des ε-transitions |
| Langages | Opérations ensemblistes, équivalence, inclusion et quotients |
| Expressions régulières | Construction de Thompson, dérivées de Brzozowski, conversions automate–expression |
| Grammaires et équations | Grammaires régulières, dérivations, lemme d’Arden et systèmes d’équations rationnelles |
| Structures algébriques | Quotients de Myhill–Nerode, automates résiduels, morphismes et monoïdes syntaxiques |
| Visualisation | DOT, SVG, PNG, PDF, TikZ, LaTeX et animation vidéo des exécutions DFA |

La disponibilité dépend du type d’automate. Le [suivi d’implémentation](docs/IMPLEMENTATION_STATUS.md) précise les méthodes publiques, leurs contraintes et les tests associés. Les [travaux à venir](docs/TD_BACKLOG.md) recensent les compléments identifiés dans les exercices du TD.

## Documentation et exemples

La **[documentation en ligne](https://optimusp-prime.github.io/Automatix/)** rassemble l’introduction, les guides et les références du projet.

- [Exemples d’utilisation](docs/EXAMPLES.md) : vingt démonstrations, des parcours aux conversions et aux exports.
- [Animation vidéo](docs/VIDEO_ANIMATION.md) : rendu d’un mot accepté ou refusé.
- [Exécutions acceptantes des NFA](docs/ACCEPTING_RUNS.md) : énumération et comptage des parcours.
- [Automates par dérivées de regex](docs/DERIVATIVE_DFA.md) : construction et limites.
- [Décisions d’architecture](docs/decisions/README.md) : choix de conception et de compatibilité.

Pour consulter ou modifier le site localement :

```bash
python -m pip install -e ".[docs]"
python -m mkdocs serve
```

La [procédure de documentation](docs/DOCUMENTATION.md) décrit la vérification et la publication sur GitHub Pages. La publication est manuelle, distincte du push des sources.

## Développement

Le code de l’extension se trouve dans `automata_extensions/`, les tests dans `tests/` et les démonstrations interactives dans `notebooks/`. Le dossier `reference/automata-lib/` contient une copie de référence de la bibliothèque amont ; il n’est pas modifié.

L’extension utilise l’héritage et des mixins par domaine. Un correctif de compatibilité appliqué à l’exécution est documenté dans [l’ADR sur `cached_method`](docs/decisions/ADR-0025-cached-method-runtime-patch.md).

Pour installer les dépendances de développement et lancer les tests :

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Les tests de rendu nécessitent les outils externes indiqués plus haut. Avant de contribuer, consultez les [règles du projet](AGENTS.md) et le [suivi d’implémentation](docs/IMPLEMENTATION_STATUS.md).
