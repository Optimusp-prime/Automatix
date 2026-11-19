# Application web Automatix

```text
web/
├── backend/     # API FastAPI : importe automata_extensions
└── frontend/    # Éditeur React + TypeScript
```

Depuis la racine du dépôt, installer la bibliothèque et les dépendances backend :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . -r web/backend/requirements-dev.txt
npm --prefix web/frontend ci
```

Lancer l'API et l'éditeur dans deux terminaux, depuis la racine :

```bash
.venv/bin/python -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000
```

```bash
npm --prefix web/frontend run dev
```

Ouvrir <http://localhost:5173>. Pour une installation sans tests, utiliser
`requirements.txt` à la place de `requirements-dev.txt`.

Le package Python publié reste limité à `automata_extensions/` ; cette application
s'exécute depuis le dépôt. Guide complet : [POC web](../docs/WEB_POC.md).
