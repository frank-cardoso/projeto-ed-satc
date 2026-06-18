from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'gustavo',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ingestao_camada_bronze',
    default_args=default_args,
    description='Processar dados brutos da Landing Zone e salvar na Bronze em Delta Lake',
    schedule='@daily',  
    start_date=datetime(2026, 6, 18),
    catchup=False,
    tags=['bronze', 'spark', 'tigris'],
) as dag:

    executar_job_bronze = BashOperator(
        task_id='executar_pyspark_bronze',
        bash_command='python /usr/local/airflow/notebooks/job_bronze.py',
    )

    executar_job_bronze