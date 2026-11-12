# Exercice 38 : executions acceptantes des NFA sans epsilon

Les deux fonctions suivantes sont accessibles depuis la classe publique
`ExtendedNFA`, sans import de mixin.

```python
from automata_extensions.fa import ExtendedNFA

nfa = ExtendedNFA(
    states={0, 1},
    input_symbols={"a", "b"},
    transitions={
        0: {"a": {0, 1}, "b": {0}},
        1: {"a": {1}, "b": {1}},
    },
    initial_state=0,
    final_states={1},
)

assert nfa.count_accepting_runs("abaa") == 3
assert set(nfa.accepting_runs("abaa")) == {
    (0, 1, 1, 1, 1),
    (0, 0, 0, 1, 1),
    (0, 0, 0, 0, 1),
}
assert nfa.count_accepting_runs("") == 0
assert nfa.intersection(nfa).count_accepting_runs("abaa") == 9
```

## Contrat

Pour un mot u de longueur n, une execution est une suite d'etats
`(q0, ..., qn)`, commencant a l'etat initial, respectant les transitions
et se terminant dans un etat final. Des chemins qui fusionnent gardent
leur multiplicite. Les destinations etant des ensembles, deux copies
identiques d'une meme transition ne sont pas representables.

- `accepting_runs(word)` retourne un iterateur progressif de tuples
  immuables. Chaque tuple contient n+1 etats. L'ordre des resultats depend
  de l'iteration des destinations ; il n'est pas garanti comme lexical.
- `count_accepting_runs(word)` retourne un entier Python exact, sans
  construire les executions. Ce nombre differe du nombre de mots acceptes.
- Le mot vide a une execution acceptante exactement lorsque l'etat initial
  est final. Un caractere inconnu ou une transition manquante donne zero.
- Chaque appel est independant et ne modifie ni l'automate ni ses caches.
- Un argument autre qu'une chaine leve `TypeError`. Toute vraie transition
  epsilon leve `ValueError`, meme si elle est inaccessible. Une entree
  `"": set()` est autorisee car elle ne represente aucune transition.
  Les erreurs sont signalees des l'appel, avant consommation de l'iterateur.

Ne pas eliminer automatiquement les epsilon-transitions pour compter les
executions de l'automate d'origine : cette transformation preserve le
langage, mais pas la multiplicite des chemins. Le present ajout ne definit
pas le comptage des chemins epsilon, notamment en presence de cycles.

## Construction mathematique

Soit c_i(q) le nombre de chemins lisant les i premiers symboles du mot et
se terminant en q. Initialement c_0(q0)=1 et c_0(q)=0 ailleurs. Pour le
symbole a_i, on calcule :

    c_(i+1)(r) = somme des c_i(q) pour les transitions q --a_i--> r
    N(A,u) = somme des c_n(f) pour f final

Cette programmation dynamique conserve les contributions des branches qui
fusionnent. Dans l'exemple, quitter 0 pour 1 choisit exactement une
occurrence de a : N(A,u)=|u|_a.

Pour deux NFA sans epsilon, le produit pour intersection associe un chemin
de chaque operande. Ainsi N(A1 intersection A2,u)=N(A1,u)*N(A2,u).
Cette identite compte les chemins, meme si un seul mot est reconnu.

## Cout et limites

Pour n caracteres, la validation prend O(|Q|+n). L'enumeration iterative
visite P extensions de prefixes et produit A tuples, pour un cout total
O(|Q|+n+P+A*(n+1)). Le nombre de prefixes et le resultat peuvent etre
exponentiels. Sa memoire auxiliaire contient O(n+1) references ; convertir
l'iterateur en liste stocke en plus tous les tuples.

Le comptage conserve deux couches de multiplicites : O(|Q|) entiers et
O(|Q|+n+somme E_i) operations avec additions supposees constantes, E_i
etant le nombre de transitions pertinentes de la couche i. Les grands
entiers ajoutent leur cout reel en bits : une addition de B bits coute
O(B), et les comptes peuvent occuper O(|Q|*B) bits.

Voir [ADR-0028](decisions/ADR-0028-epsilon-free-accepting-runs.md) et
`tests/fa/test_accepting_runs.py`. Cette fonctionnalite complete le TD 38 ;
elle n'ajoute pas de conversion par derivees ni de fonctions sur GNFA/DFA.
