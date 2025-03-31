import sys
import os
import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from utils import common, gcp_big_query, gcp_cloud_storage, velib_file_registry
from utils.config import *
from utils.velib_file_registry import register_file
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowSkipException


# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    dag_id="hourly_ingestion_velib_dag",
    default_args=default_args,
    description="Hourly DAG to download and process Velib data",
    #schedule_interval="*/30 * * * *",
    schedule_interval="@hourly",
    start_date=days_ago(1),
    catchup=False,
)

#### === Only Run after the Init Dag ==== ####
def check_init_complete(**kwargs):
    init_status = Variable.get("init_complete", default_var=False)
    if not init_status or init_status.lower() != "true":
        raise AirflowSkipException("Initialization not complete yet.")
    return "Initialization already completed."

check_init_task = PythonOperator(
    task_id="check_init_complete",
    python_callable=check_init_complete,
    dag=dag,
)

#### === Download and Upload Parquet Files ==== ####
def hourly_download_upload(**kwargs):

    # Download and upload velib data
    file_timestamp = common.get_paris_timestamp()
    velib_filename = f"velib_{file_timestamp}.parquet"

    gcp_cloud_storage.download_file(velib_url, velib_filename)
    gcp_cloud_storage.upload_file(velib_filename)
    gcp_cloud_storage.remove_local_file(velib_filename)

    # Insert into the file registry table
    register_file(velib_filename)

    return "Velib data uploaded successfully."

hourly_download_upload_task = PythonOperator(
    task_id="hourly_download_upload",
    python_callable=hourly_download_upload,
    provide_context=True,
    dag=dag,
)

#### === Update External, Native and File Registry Tables ==== ####
def process_unprocessed_files(**kwargs):
    result = gcp_big_query.process_unprocessed_files()
    return result

process_unprocessed_files_task = PythonOperator(
    task_id="process_unprocessed_files",
    python_callable=process_unprocessed_files,
    provide_context=True,
    dag=dag,
)

# Define the task dependencies
check_init_task >> hourly_download_upload_task >> process_unprocessed_files_task
