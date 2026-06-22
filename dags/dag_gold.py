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
    "processamento_camada_gold",
    default_args=default_args,
    description="Processar dados da Silver e salvar a camada Gold em Delta Lake",
    schedule="@daily",
    start_date=datetime(2026, 6, 18),
    catchup=False,
    tags=["gold", "spark", "tigris"],
) as dag:

    executar_job_gold = BashOperator(
        task_id="executar_pyspark_gold",
        bash_command="python /usr/local/airflow/notebooks/job_gold.py",
    )

    executar_job_gold
