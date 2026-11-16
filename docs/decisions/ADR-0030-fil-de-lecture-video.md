# ADR-0030 — Présentation vidéo « Fil de lecture »

Status: Accepted
Date: 2026-11-16

## Contexte

L'utilisateur a validé le croquis « Fil de lecture » puis demandé des mouvements
moins mécaniques et un suffixe souligné rouge, à pleine opacité, lors d'un refus.
Le titre, le panneau encadré, la légende du mot et les badges remplis n'apportaient
pas d'information utile.

## Décision

Conserver le placement Graphviz unique, la composition Pillow suréchantillonnée,
FFmpeg et les cadences publiques d'ADR-0027. Changer uniquement la présentation.
Le mot occupe l'angle supérieur gauche. Les caractères consommés sont composés
à 25 % d'opacité sur le fond ; le suffixe refusé reste à 100 % avec traits rouges.
Le verdict visible est toujours « Refusé » pour les deux formes de rejet.

Une phase continue par étape pilote une interpolation quintique de la distance
sur la spline, une pulsation du caractère, le fondu source/destination et le halo
d'arrivée. Une boucle conserve son état actif pendant le mouvement. Le compteur
privé `step` compte désormais les caractères effectivement consommés : une
transition absente n'incrémente jamais ce nombre.

Un refus après lecture complète utilise le dernier caractère comme repère visuel
du verdict ; il ne transforme pas cette transition valide en transition absente.
Pour ε, seul le verdict porte la couleur du résultat.

## Conséquences

Aucun nouvel argument public, changement du langage reconnu, mutation de l'objet
ou dépendance. Les exports graphiques et le lecteur HTML restent inchangés.
Les mots longs ont une fenêtre de 18 caractères ; l'affichage n'implique pas
consommation des caractères masqués. Les polices de quelques tailles sont des
ressources locales à un export, pas des caches d'algorithmes sur les automates.

## Supersedes

ADR-0027 seulement pour le marqueur mobile, les cartes de caractères et le badge
rempli. Son architecture et ses garanties d'encodage restent en vigueur.
