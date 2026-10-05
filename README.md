# GEAAI

dev server - [dev-erp.thegeaai.com](dev-erp.thegeaai.com)

```docker compose run web odoo -u people_directory,ica_mm_nrc -d geaai_odoo_19e --no-http```

## Development Checks

Install development tools:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Run the same Ruff checks used by CI/CD:

```bash
ruff check .
ruff format --check .
```

Auto-format Python files:

```bash
ruff format .
```
