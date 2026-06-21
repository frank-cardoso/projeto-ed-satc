from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


default_args = {
    "owner": "gustavo",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "processamento_camada_silver",
    default_args=default_args,
    description="Processar dados da Bronze e salvar a camada Silver em Delta Lake",
    schedule="@daily",
    start_date=datetime(2026, 6, 18),
    catchup=False,
    tags=["silver", "spark", "tigris"],
) as dag:

    executar_job_silver = BashOperator(
        task_id="executar_pyspark_silver",
        bash_command="python /usr/local/airflow/notebooks/job_silver.py",
    )

    executar_job_silver
