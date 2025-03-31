import sys
import os
import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from utils import common, gcp_big_query, gcp_cloud_storage, velib_file_registry
from utils.config import *
from utils.velib_file_registry import register_file
from airflow.utils.dates import days_ago
from airflow.models import Variable

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    dag_id="init_ingestion_velib_arr_dag",
    default_args=default_args,
    description="Initialization DAG for arrondissement data and initial Velib load",
    schedule_interval="@once",
    # Only run once and do not catch up
    start_date=days_ago(1),
    catchup=False,
)
#### === Set Local Environment Variables ==== ####
### Uncomment these lines if running locally.
### When running on Google Composer, the variables are already set in Terraform.
def set_gcp_variables(**kwargs):
    Variable.set("project", "<your-gcp-project-id>")
    Variable.set("bucket_name", "velib-data-bucket")
    Variable.set("region", "us-east1-b")
    Variable.set("dataset_name", "velib_dataset")
    return "Set Environment Variables"

set_gcp_variables_task = PythonOperator(
    task_id="set_gcp_variables",
    python_callable=set_gcp_variables,
    dag=dag,
)

#### === Create File Registry Table ==== ####
def create_file_registry_table(**kwargs):
    result = velib_file_registry.create_file_registry_table()
    return result

create_registry_task = PythonOperator(
    task_id="create_file_registry_table",
    python_callable=create_file_registry_table,
    provide_context=True,
    dag=dag,
)
#### === Download and Upload Parquet Files ==== ####
def init_download_upload(**kwargs):
    # Download and upload arrondissement data
    gcp_cloud_storage.download_file(arrondissement_url, arrondissement_filename)
    gcp_cloud_storage.upload_file(arrondissement_filename)
    gcp_cloud_storage.remove_local_file(arrondissement_filename)

    # Download and upload velib data
    gcp_cloud_storage.download_file(velib_url, init_velib_filename)
    gcp_cloud_storage.upload_file(init_velib_filename)
    gcp_cloud_storage.remove_local_file(init_velib_filename)

    # Insert into the file registry table
    register_file(init_velib_filename)

    return "District and initial Velib data uploaded successfully."

init_download_upload_task = PythonOperator(
    task_id="init_download_upload",
    python_callable=init_download_upload,
    # Context variables are passed as keyword arguments
    provide_context=True,
    dag=dag,
)

#### === Create External and Native Tables ==== ####
def init_create_external_and_native_tables(**kwargs):
    result = gcp_big_query.create_external_table("arrondissement")
    result = gcp_big_query.create_external_table("velib")

    result = gcp_big_query.create_native_table("arrondissement")
    # Including the logic to update the file registry table
    result = gcp_big_query.create_native_table("velib")
    return result

init_create_external_and_native_tables_task = PythonOperator(
    task_id="init_create_external_and_native_tables",
    python_callable=init_create_external_and_native_tables,
    provide_context=True,
    dag=dag,
)

#### === Confirm the completion of the tasks ==== ####
def mark_init_complete(**kwargs):
    Variable.set("init_complete", True)
    return "Initialization complete"

mark_init_complete_task = PythonOperator(
    task_id="mark_init_complete",
    python_callable=mark_init_complete,
    dag=dag,
)

# Define the task dependencies
set_gcp_variables_task >> create_registry_task >> init_download_upload_task >> init_create_external_and_native_tables_task >> mark_init_complete_task
