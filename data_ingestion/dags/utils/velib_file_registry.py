from google.cloud import bigquery
from utils.config import *

BQ_CLIENT = bigquery.Client()

def execute_query(query: str, parameters: list = None):
    if parameters:
        job_config = bigquery.QueryJobConfig(query_parameters=parameters)
        return BQ_CLIENT.query(query, job_config=job_config).result()
    else:
        return BQ_CLIENT.query(query).result()

def create_file_registry_table():
    ddl = f"""
    create table if not exists `{registry_table}` (
        file_name string,
        process_status string,
        ingestion_timestamp timestamp,
        last_updated timestamp,
        error_message string
    )
    """
    try:
        # Execute the query and wait for the job to complete
        BQ_CLIENT.query(ddl).result()
        message = "File Registry Table created successfully."
        print(message)
    except Exception as e:
        message = f"Error: {e}"
        print(message)
    return message

def register_file(filename: str):

    # Check if the file is already registered
    check_query = f"""
        SELECT count(1) as count 
        FROM `{registry_table}` 
        WHERE file_name = @filename
    """
    check_result = execute_query(check_query, [
        bigquery.ScalarQueryParameter("filename", "STRING", filename)
    ])
    file_count = list(check_result)[0].count

    if file_count == 0:
        # Insert a new record
        insert_query = f"""
            INSERT INTO `{registry_table}` (file_name, process_status, ingestion_timestamp, last_updated, error_message)
            VALUES (@filename, 'PENDING', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), '')
        """
        execute_query(insert_query, [
            bigquery.ScalarQueryParameter("filename", "STRING", filename)
        ])
        message = f"File {filename} registered successfully."
    else:
        message = f"File {filename} is already registered."

    print(message)
    return message

# TBD: init run wont be able to update the process status
def init_mark_files_as_processed():
    update_query = f"""
    update `{registry_table}` 
    set process_status = 'PROCESSED', last_updated = current_timestamp()
    where file_name in (
        select distinct _file_name from `{external_velib_table}`)
    """
    BQ_CLIENT.query(update_query).result()
    message = "Marked all files as processed."
    print(message)
    return message
    

def mark_files_as_processed(file_name:str):
    update_query = f"""
    update `{registry_table}` 
    set process_status = 'PROCESSED', last_updated = current_timestamp()
    where file_name = @file_name
    """
    execute_query(update_query, [
        bigquery.ScalarQueryParameter("file_name", "STRING", file_name)
    ])
    message = f"Marked file {file_name} as processed."
    print(message)
    return message

def mark_files_as_failed(file_name:str, error_message:str):
    update_query = f"""
    update `{registry_table}`
    set process_status = 'FAILED', last_updated = current_timestamp(), error_message = @error_message
    where file_name = @file_name
    """
    execute_query(update_query, [
        bigquery.ScalarQueryParameter("error_message", "STRING", error_message),
        bigquery.ScalarQueryParameter("file_name", "STRING", file_name)
    ])

    message = f"Marked file {file_name} as failed. Check error message: {error_message}"
    print(message)
    return message

def get_unprocessed_files():
    select_query = f"""
    select file_name from `{registry_table}` where process_status = 'PENDING'
    """
    results = execute_query(select_query)
    return [row.file_name for row in results]