# Vidéo « Fil de lecture » — design validé

Le croquis interactif et ses corrections ont été approuvés dans la conversation
le 16 novembre 2026, avec demande explicite d'implémentation.

## Intention

Une vidéo sobre où seuls le mot, le graphe et le verdict portent l'information.
Mot en haut à gauche, sans titre ni légende. Symboles lus à 25 % d'opacité ;
symbole courant légèrement pulsé, fond discret et trait inférieur.
Graphe fixe, tracé progressif des transitions avec accélération/décélération,
fondu entre états et halo léger à l'arrivée. Aucun gros marqueur mobile.

Le verdict final est « Accepté » ou « Refusé », accompagné d'une coche/croix.
Transition absente : arrêt au dernier état réel, soulignement rouge et opacité
100 % du symbole bloquant et de tout le suffixe non lu. Aucun état puits ajouté.
Refus en état non final après lecture complète : dernier symbole souligné rouge
à 100 %, repère du verdict, sans prétendre que sa transition était invalide.
Mot vide : ε puis verdict ; pas de faux symbole refusé.

## Approches

Trois croquis : Ligne claire (traits simples), Focus (état plein et point
mobile), Fil de lecture (soulignements et fond discret). L'utilisateur a choisi
Fil de lecture puis demandé un mouvement moins mécanique et le marquage rouge
du suffixe refusé. Le libellé « Bloqué » a été explicitement remplacé par « Refusé ».

## Architecture et limites

Conserver Graphviz pour l'unique placement, Pillow pour les images et FFmpeg
pour MP4. Modifier uniquement la présentation vidéo privée et sa timeline.
API `export_animation_video(word, filename, *, fps=1.0, render_fps=30)` inchangée,
ainsi que `animate()` HTML. Aucun changement de langage reconnu ni mutation.
1280×720, traits et labels de l'automate conservés, rendu suréchantillonné 2×.
Fenêtre glissante pour mots longs, sans réduire les caractères à l'illisible.
Choix d'implémentation : fond ivoire, accent vert canard, rouge doux et cadence
publique existante. Les ellipses indiquent les caractères hors champ.

## Vérification

Tester prefixe consommé/suffixe refusé, refus final, mot vide, mouvement
intermédiaire, boucle, transition absente, mots longs et cadre stable.
Suite pytest complète, mypy strict, vrais MP4 acceptation/refus/blocage et
inspection de leurs images. Dépendances et encodage atomique inchangés.
