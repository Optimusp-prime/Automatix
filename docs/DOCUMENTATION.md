# Contribuer à la documentation

Le site utilise **MkDocs 1.6** et son thème intégré, avec une navigation
et une recherche en français. Il lit directement les fichiers de `docs/` :
les guides, le suivi et les ADR n'ont pas de copie à synchroniser.

## Installation

À la racine du dépôt, dans votre environnement Python 3.11 ou plus :

```bash
python -m pip install -e ".[docs]"
```

L'extra `docs` ajoute MkDocs ; il n'ajoute rien à l'installation normale
de la bibliothèque. Pour travailler sur le code et la documentation ensemble :

```bash
python -m pip install -e ".[dev,docs]"
```

## Aperçu local

```bash
python -m mkdocs serve
```

Ouvrez l'adresse locale affichée, généralement `http://127.0.0.1:8000`.
MkDocs reconstruit les pages après chaque modification. Arrêtez le serveur
avec `Ctrl+C`.

## Construction et vérification

```bash
python -m mkdocs build --strict
```

Le résultat est placé dans `site/`, ignoré par Git. Les avertissements de
construction, notamment les liens internes ou ancres introuvables, font
échouer cette commande. Elle ne vérifie pas la disponibilité des sites externes.

Le site généré peut être consulté avec un serveur local :

```bash
python -m http.server 8000 --directory site
```

Aucune publication ni configuration d'hébergement n'est activée. Une future
publication devra fixer l'adresse canonique `site_url` dans `mkdocs.yml`.

## Ajouter ou modifier une page

1. Modifiez le fichier Markdown existant dans `docs/`, ou ajoutez une page.
2. Si elle constitue une entrée principale, ajoutez-la à `nav` dans `mkdocs.yml`.
3. Utilisez des liens relatifs vers les autres fichiers `.md` et les images.
4. Lancez la construction stricte, puis consultez le rendu local.

Les ADR sont accessibles depuis leur [index](decisions/README.md) et la
recherche. Ils n'encombrent pas la navigation principale. Conservez les
décisions acceptées ; une modification d'architecture nécessite un nouvel ADR.

La page [API et suivi](IMPLEMENTATION_STATUS.md) reste la référence pour les
statuts des fonctionnalités. Les tâches du TD restent dans le
[backlog](TD_BACKLOG.md). La création de ce site ne change pas leurs statuts.

## Références de configuration

- [Configuration MkDocs](https://www.mkdocs.org/user-guide/configuration/).
- [Organisation et liens des pages](https://www.mkdocs.org/user-guide/writing-your-docs/).
