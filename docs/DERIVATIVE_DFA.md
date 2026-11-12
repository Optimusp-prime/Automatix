# Automate construit par dérivées d'expression régulière

`Regex.to_dfa()` complète le calcul des dérivées déjà disponible : la méthode
construit directement un `ExtendedDFA`, utilisable avec les opérations et
les exports habituels.

```python
from automata_extensions.regex import Regex

expression = Regex("ab|ac", input_symbols={"a", "b", "c"})
automate = expression.to_dfa()

assert automate.is_complete()
assert automate.accepts("ab")
assert automate.accepts("ac")
assert not automate.accepts("a")

apres_a = automate.transitions[automate.initial_state]["a"]
assert str(apres_a) == "b|c"
minimal = automate.minimize()
assert minimal.is_equivalent(automate)
```

## Construction mathématique

Un état représente une expression dérivée : après avoir lu u, il reconnaît
les suffixes v tels que uv appartient au langage initial. La transition
étiquetée a conduit à la dérivée par a. Un état est accepteur si son
expression contient le mot vide.

Le parcours en largeur explore les seuls états accessibles et crée une
transition pour chaque symbole de l'alphabet mémorisé dans `Regex`. Une
dérivée vide accessible devient un état puits rejetant. L'alphabet vide
est autorisé : un unique état sans transition est alors complet.

La normalisation interne rassemble les termes d'une union, supprime les
doublons et fixe leur ordre. Elle traite aussi l'associativité de la
concaténation, les identités du mot vide et du langage vide, et les étoiles
triviales ou imbriquées. La similarité des expressions suffit à rendre
finie l'exploration ; elle ne reconnaît pas nécessairement toutes les
équivalences de langages. Le résultat n'est donc pas garanti minimal.
Voir Owens, Reppy et Turon, section 4.1, dans les références ci-dessous.

## Contrats et limites

- Les états sont des objets `Regex` immuables, pas des noms artificiels.
  L'état initial est la forme normalisée de l'expression source.
- La source et les résultats existants de `derivative()` restent inchangés.
  Chaque conversion produit un nouvel automate sans cache persistant.
- La méthode réutilise les dérivées ; elle n'appelle ni Thompson, ni une
  construction par sous-ensembles, ni un test d'équivalence de langages.
- La syntaxe reste celle de `Regex` : `|`, concaténation implicite, `*`,
  parenthèses et `()` ou chaîne vide pour epsilon. L'alphabet explicite
  contient des caractères uniques et doit inclure tous les littéraux.
  La notation mathématique `+` du TD doit être transcrite en `|`.
- Les expressions 4 et 5 du TD 51 utilisent c et d malgré l'alphabet
  annoncé dans l'introduction de l'exercice : ces caractères doivent être
  inclus dans l'alphabet choisi pour les convertir.
- `str(regex)` est un affichage diagnostique, pas une sérialisation. Le
  littéral `∅` et le langage vide interne peuvent s'afficher pareil ; la
  construction les distingue par leur structure, sans reparsing du texte.
- La récursion des opérations sur l'AST impose la limite habituelle de
  profondeur de Python. Le nombre d'états et la taille des expressions
  peuvent croître fortement. Un alphabet Unicode est possible mais est
  parcouru caractère par caractère, sans regroupement en classes.

## Coût et validation

Pour R états atteignables et s symboles, le graphe contient R*s transitions.
Le coût est O(s log s + R*s + C + V), où C regroupe les calculs réels de
dérivées, normalisation, comparaison structurelle, tri, hachage et
nullabilité, et V la construction du DFA. La mémoire comprend le graphe,
les AST retenus et leur espace de calcul temporaire. Le coût par transition
n'est pas supposé constant ; une croissance exponentielle est possible.

`tests/regex/test_derivative_dfa.py` compare les langages obtenus avec
automata-lib et la construction de Thompson d'Automatix. Les autres tests
vérifient les états dérivés, la complétude, les cas vides, Unicode, la
normalisation, l'immuabilité et l'absence de conversion intermédiaire.

## Références

- INF302, Enonce_TD.v04, exercice 51.
- [Brzozowski (1964), Derivatives of Regular Expressions](https://doi.org/10.1145/321239.321249).
- [Owens, Reppy et Turon (2009), Regular-expression derivatives re-examined](https://doi.org/10.1017/S0956796808007090), section 4.1.
- [ADR-0029](decisions/ADR-0029-derivative-dfa-normal-forms.md).
