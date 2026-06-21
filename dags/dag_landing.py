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
    "ingestao_camada_landing",
    default_args=default_args,
    description="Extrair dados do MongoDB Atlas e salvar na Landing Zone do Tigris",
    schedule="@daily",
    start_date=datetime(2026, 6, 18),
    catchup=False,
    tags=["landing", "mongo", "tigris"],
) as dag:

    executar_job_landing = BashOperator(
        task_id="executar_python_landing",
        bash_command="python /usr/local/airflow/notebooks/job_landing.py",
    )

    executar_job_landing
