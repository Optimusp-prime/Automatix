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

## Publication sur GitHub Pages

Adresse du site : <https://optimusp-prime.github.io/Automatix/>.
Elle figure aussi dans la rubrique **About** du dépôt GitHub.

Après avoir vérifié les modifications, publiez depuis la racine du projet :

```bash
python -m mkdocs gh-deploy --strict
```

Cette commande construit le site et pousse uniquement les fichiers générés
sur la branche `gh-pages`. GitHub Pages utilise cette branche, à sa racine.
Elle ne committe ni ne pousse les modifications des fichiers source : ceux-ci
restent à enregistrer sur la branche de travail et à intégrer par PR.
La publication est manuelle ; un simple push sur `main` ne republie pas le site.

## Ajouter ou modifier une page

1. Modifiez le fichier Markdown existant dans `docs/`, ou ajoutez une page.
2. Si elle constitue une entrée principale, ajoutez-la à `nav` dans `mkdocs.yml`.
3. Utilisez des liens relatifs vers les autres fichiers `.md` et les images.
4. Lancez la construction stricte, puis consultez le rendu local.

Les ADR sont accessibles depuis leur [index](decisions/README.md) et la
recherche. Ils n'encombrent pas la navigation principale. Conservez les
décisions acceptées ; une modification d'architecture nécessite un nouvel ADR.

La barre principale contient seulement les rubriques **Guides** et
**Référence**, en plus de la recherche, du code source et du choix de thème.
Le nom **Automatix** ramène à l'introduction. Celle-ci, le backlog et cette
page restent publiés et indexés, sans entrée dédiée dans la barre.
Le fichier `docs_theme/main.html` conserve ce lien vers l'introduction et
retire les raccourcis précédent/suivant de la barre. Les adaptations mobiles
et la présentation de l'introduction sont dans `docs/assets/documentation.css`.

Après une modification de navigation, vérifiez le menu repliable et ses
sous-menus sur téléphone et tablette, ainsi que la barre sur ordinateur.
Les titres longs doivent revenir à la ligne et le menu ouvert doit pouvoir
défiler sur un écran de faible hauteur. Vérifiez aussi le retour à
l'introduction depuis une page de guide via le nom Automatix.

La page [API et suivi](IMPLEMENTATION_STATUS.md) reste la référence pour les
statuts des fonctionnalités. Les tâches du TD restent dans le
[backlog](TD_BACKLOG.md). La création de ce site ne change pas leurs statuts.

## Références de configuration

- [Configuration MkDocs](https://www.mkdocs.org/user-guide/configuration/).
- [Organisation et liens des pages](https://www.mkdocs.org/user-guide/writing-your-docs/).
