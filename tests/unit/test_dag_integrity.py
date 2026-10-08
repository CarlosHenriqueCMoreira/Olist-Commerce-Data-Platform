"""O DAG carrega e mantém a ordem esperada.

Roda num subprocesso fora da raiz do repo: a pasta airflow/ do projeto sombrearia o pacote
`airflow` real. Pulado se o Airflow não estiver instalado no Python atual.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

DAG_DIR = Path(__file__).resolve().parents[2] / "airflow" / "dags"

SCRIPT = textwrap.dedent("""
    import sys
    try:
        from airflow.models import DagBag
    except ImportError:
        sys.exit(3)
    bag = DagBag(dag_folder=sys.argv[1], include_examples=False)
    assert not bag.import_errors, bag.import_errors
    dag = bag.dags["olist_pipeline"]
    order = ["check_files", "validate_sources", "load_raw", "dbt_staging",
             "dbt_intermediate", "dbt_marts", "dbt_tests", "export_dashboard_data"]
    assert [t.task_id for t in dag.topological_sort()] == order
    assert all(t.retries == 2 for t in dag.tasks)
    assert dag.get_task("export_dashboard_data").upstream_task_ids == {"dbt_tests"}
    """)


def test_dag_loads_with_expected_order(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", SCRIPT, str(DAG_DIR)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 3:
        pytest.skip("Airflow não instalado")
    assert result.returncode == 0, result.stderr[-2000:]
