# Automatix

Ce projet étend automata-lib 9.2.0 sans modifier la bibliothèque originale.

Notre code se trouve dans `automata_extensions/`. La copie de référence
upstream se trouve dans `reference/automata-lib/`, au tag `v9.2.0`, et doit
rester intacte. Le notebook se trouve dans `notebooks/sandbox.ipynb`.

## Installation

```powershell
conda activate automate-env-clean
python -m pip install -e .
```

Pour installer également la dépendance de développement pytest :

```powershell
python -m pip install -e ".[dev]"
```

## Tests

```powershell
python -m pytest
```

Seuls les tests du dossier `tests/` sont collectés par défaut.

## Import

```python
from automata_extensions.fa import ExtendedDFA
```
