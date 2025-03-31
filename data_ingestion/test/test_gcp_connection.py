from datetime import datetime
from airflow import DAG
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator
from utils.config import *

default_args = {
    'start_date': datetime(2023, 1, 1),
    'catchup': False,
}

with DAG(
    'test_gcp_connection_dag',
    default_args=default_args,
    schedule_interval=None,
) as dag:

    list_files = GCSListObjectsOperator(
        task_id='list_gcs_files',
        bucket=bucket_name,
        gcp_conn_id='google_cloud_default',  
    )
