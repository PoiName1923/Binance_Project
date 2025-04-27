from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from loading_postgres import *

default_args = {
    'owner': 'Loading Daily Batch Data',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'daily_crypto_data_loader',
    default_args=default_args,
    schedule_interval='0 0 * * *',
    catchup=False,
    tags=['crypto', 'data_pipeline'],
) as dag:
    
    load_task = PythonOperator(
        task_id='load_daily_data_to_postgres',
        python_callable=loading_daily_data,
        provide_context=True,
    )
    
    load_task