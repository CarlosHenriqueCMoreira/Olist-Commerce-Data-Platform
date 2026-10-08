"""DAG do pipeline Olist: arquivos -> raw -> dbt (staging, intermediate, marts) -> testes -> export.

Execução manual (o dataset é histórico; não há agenda). Cada etapa chama o venv do projeto
(/home/airflow/olist-venv), então o DAG só depende do Airflow. Credenciais vêm de variáveis de
ambiente do container (POSTGRES_*), nunca do código.

Uma falha em qualquer task (inclusive `dbt test` com status error) interrompe o DAG:
`export_dashboard_data` só roda se todos os testes passaram.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

PROJECT = "/opt/olist"
VENV = "/home/airflow/olist-venv/bin"
PY = f"cd {PROJECT} && {VENV}/python -m src.cli"
# profiles.yml é gitignored: cria a partir do exemplo (lê POSTGRES_* do ambiente)
DBT_PREP = f"cd {PROJECT}/dbt_project && cp -n profiles.yml.example profiles.yml || true"
DBT = f"{DBT_PREP} && {VENV}/dbt"
DBT_FLAGS = "--profiles-dir . --target-path /tmp/dbt_target --log-path /tmp/dbt_logs"

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=20),
}

with DAG(
    dag_id="olist_pipeline",
    description="Olist Commerce Data Platform: ingestão, dbt e testes de qualidade",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["olist", "dbt", "postgres"],
    doc_md=__doc__,
) as dag:
    check_files = BashOperator(task_id="check_files", bash_command=f"{PY} check-files")
    validate_sources = BashOperator(task_id="validate_sources", bash_command=f"{PY} validate")
    # imprime linhas carregadas/ignoradas por tabela no log da task
    load_raw = BashOperator(task_id="load_raw", bash_command=f"{PY} load")
    dbt_staging = BashOperator(
        task_id="dbt_staging", bash_command=f"{DBT} run --select staging {DBT_FLAGS}"
    )
    dbt_intermediate = BashOperator(
        task_id="dbt_intermediate", bash_command=f"{DBT} run --select intermediate {DBT_FLAGS}"
    )
    dbt_marts = BashOperator(
        task_id="dbt_marts", bash_command=f"{DBT} run --select marts {DBT_FLAGS}"
    )
    # testes de todas as camadas; severidade 'error' falha a task e bloqueia o export
    dbt_tests = BashOperator(task_id="dbt_tests", bash_command=f"{DBT} test {DBT_FLAGS}")
    export_dashboard_data = BashOperator(
        task_id="export_dashboard_data", bash_command=f"{PY} export"
    )

    (
        check_files
        >> validate_sources
        >> load_raw
        >> dbt_staging
        >> dbt_intermediate
        >> dbt_marts
        >> dbt_tests
        >> export_dashboard_data
    )
