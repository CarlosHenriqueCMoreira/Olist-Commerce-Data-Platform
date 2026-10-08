SHELL := /bin/bash
PY ?= .venv/bin/python
DBT := set -a && . ./.env && set +a && cd dbt_project && DBT_PROFILES_DIR=. ../.venv/bin/dbt
ENV := set -a && . ./.env && set +a &&

.PHONY: sample-data help setup up down logs psql ingest validate pipeline dbt-build dbt-docs test lint format dashboard export clean

help:  ## lista os comandos
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

setup:  ## cria .venv, instala dependências e prepara .env/profiles
	python3.11 -m venv .venv || python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@test -f .env || cp .env.example .env
	@test -f dbt_project/profiles.yml || cp dbt_project/profiles.yml.example dbt_project/profiles.yml
	@echo "Edite POSTGRES_PASSWORD no .env se quiser trocar a senha."

dbt_project/profiles.yml:
	cp dbt_project/profiles.yml.example dbt_project/profiles.yml

up:  ## sobe o PostgreSQL (Docker) e espera o healthcheck
	docker compose up -d --wait postgres

down:  ## para os containers (mantém os dados)
	docker compose down

logs:  ## logs do PostgreSQL
	docker compose logs -f postgres

psql:  ## abre um psql dentro do container
	@$(ENV) docker compose exec postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB

validate:  ## valida os CSVs em data/raw
	@$(ENV) $(PY) -m src.cli validate

ingest:  ## carrega os CSVs no schema raw (idempotente)
	@$(ENV) $(PY) -m src.cli load

dbt-build: dbt_project/profiles.yml  ## dbt build (modelos + testes)
	@$(DBT) build

dbt-docs: dbt_project/profiles.yml  ## gera e serve a documentação dbt
	@$(DBT) docs generate && $(DBT) docs serve

export:  ## exporta os marts para data/exports
	@$(ENV) $(PY) -m src.cli export

pipeline: up ingest dbt-build export  ## pipeline completo: sobe DB, ingere, constrói e testa

test:  ## pytest (testes de integração rodam se o PostgreSQL estiver acessível)
	@$(ENV) $(PY) -m pytest -q

lint:  ## ruff + black --check
	.venv/bin/ruff check . && .venv/bin/black --check .

format:  ## formata o código
	.venv/bin/ruff check --fix . && .venv/bin/black .

dashboard:  ## abre o dashboard Streamlit
	@$(ENV) .venv/bin/streamlit run dashboard/app.py

clean:  ## ATENÇÃO: apaga o volume do PostgreSQL (todos os dados carregados)
	@echo "!! Isto remove o volume local do banco (raw, staging, intermediate, marts)."
	@read -p "Digite 'sim' para continuar: " ans && [ "$$ans" = "sim" ] && docker compose down -v || echo "Cancelado."

sample-data:  ## gera dataset sintético em data/sample (sem baixar o Kaggle)
	$(PY) scripts/generate_sample_data.py data/sample
