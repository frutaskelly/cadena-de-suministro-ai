# Cadena de Suministro AI — comandos útiles para desarrollo local

.PHONY: help db-start db-stop db-status db-reset migrate seed seed-all seed-sat sinonimos fuzzy-pedidos run test demo

help:
	@echo "Comandos disponibles:"
	@echo "  make db-start       - Arranca Postgres local en :5433"
	@echo "  make db-stop        - Apaga Postgres local"
	@echo "  make db-status      - Estado de Postgres local"
	@echo "  make db-reset       - Borra y recrea la base (¡destructivo!)"
	@echo "  make migrate        - Aplica migraciones Alembic"
	@echo "  make seed           - Migra datos de Frutas Kelly al backend"
	@echo "  make seed-sat       - Seed de catálogos SAT (regimenes, usos CFDI, etc.)"
	@echo "  make sinonimos      - Importa sinónimos del agente legacy"
	@echo "  make fuzzy-pedidos  - Re-procesa pedidos sin matchear con fuzzy"
	@echo "  make seed-all       - seed + seed-sat + sinonimos + fuzzy-pedidos"
	@echo "  make run            - Arranca backend FastAPI en :8000"
	@echo "  make test           - Corre tests pytest"
	@echo "  make demo           - Pipeline completo: db + migrate + seed-all + tests"

PG_BIN := /opt/homebrew/opt/postgresql@16/bin
PG_DATA := pgdata

db-start:
	@LC_ALL=C $(PG_BIN)/pg_ctl -D ./$(PG_DATA) -l ./pgdata.log -o "-p 5433 -k /tmp" start || true
	@sleep 1
	@$(PG_BIN)/psql -h /tmp -p 5433 -U postgres -d cadena_dev -c 'SELECT 1' >/dev/null 2>&1 && echo "✓ Postgres corriendo en :5433" || (echo "Creando DB..." && $(PG_BIN)/psql -h /tmp -p 5433 -U postgres -c 'CREATE DATABASE cadena_dev;')

db-stop:
	@LC_ALL=C $(PG_BIN)/pg_ctl -D ./$(PG_DATA) stop || true

db-status:
	@LC_ALL=C $(PG_BIN)/pg_ctl -D ./$(PG_DATA) status || true

db-reset:
	@read -p "¿Seguro que quieres borrar TODO en cadena_dev? [y/N] " ans && [ "$$ans" = "y" ]
	@$(PG_BIN)/psql -h /tmp -p 5433 -U postgres -c 'DROP DATABASE IF EXISTS cadena_dev;'
	@$(PG_BIN)/psql -h /tmp -p 5433 -U postgres -c 'CREATE DATABASE cadena_dev;'
	@echo "✓ DB reseteada. Corre 'make migrate' para recrear schema."

migrate:
	@cd backend && . venv/bin/activate && alembic upgrade head

seed:
	@cd backend && . venv/bin/activate && python ../scripts/migrate_frutas_kelly.py

seed-sat:
	@cd backend && . venv/bin/activate && python ../scripts/seed_sat_catalogs.py

sinonimos:
	@cd backend && . venv/bin/activate && python ../scripts/import_sinonimos.py

fuzzy-pedidos:
	@cd backend && . venv/bin/activate && python ../scripts/match_unmatched_pedidos.py

seed-all: seed seed-sat sinonimos fuzzy-pedidos

run:
	@cd backend && . venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	@cd backend && . venv/bin/activate && pytest tests/ -v

demo: db-start migrate seed-all test
	@echo ""
	@echo "✅ Demo lista. Ahora:"
	@echo "  - make run                       # arranca backend"
	@echo "  - http://localhost:8000/         # operator dashboard"
	@echo "  - http://localhost:8000/docs     # API interactiva"
