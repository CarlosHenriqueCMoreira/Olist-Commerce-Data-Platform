FROM apache/airflow:2.10.5-python3.11

# O código do projeto roda num venv próprio (SQLAlchemy 2, dbt, pandas) para não
# conflitar com as dependências fixadas pelo Airflow. O DAG só chama esse venv via bash.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /home/airflow/olist-venv \
    && /home/airflow/olist-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
