import os
import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from utils.config import *

# Set the absolute path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DBT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "data_transformation")
DBT_PROFILES_DIR = DBT_PROJECT_DIR

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    dag_id="daily_dbt_transformation_dag",
    default_args=default_args,
    description="Daily DAG to run dbt transformations",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
)

# Define the dbt run command
dbt_run_cmd = f"""
cd {DBT_PROJECT_DIR} && \
dbt run --profiles-dir {DBT_PROFILES_DIR}
"""

# Define the dbt test command
dbt_test_cmd = f"""
cd {DBT_PROJECT_DIR} && \
dbt test --profiles-dir {DBT_PROFILES_DIR}
"""

#  Run dbt models
dbt_run_task = BashOperator(
    task_id='dbt_run',
    bash_command=f"dbt run --profiles-dir {DBT_PROFILES_DIR}",
    cwd=DBT_PROJECT_DIR,  # This sets the working directory for the command
    dag=dag,
)

# Test dbt models
dbt_test_task = BashOperator(
    task_id='dbt_test',
    bash_command=f"dbt test --profiles-dir {DBT_PROFILES_DIR}",
    cwd=DBT_PROJECT_DIR,  # This sets the working directory for the command
    dag=dag,
)

# Define task dependencies
dbt_run_task >> dbt_test_task
