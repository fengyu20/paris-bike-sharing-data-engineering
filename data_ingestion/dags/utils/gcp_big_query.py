from google.cloud import bigquery
from utils.config import *
from utils.velib_file_registry import *

# Create a BigQuery client
BQ_CLIENT = bigquery.Client()

def create_external_table(table_type: str):

    if table_type == "velib":
        table_name = external_velib_table
        uri_pattern = f"gs://{bucket_name}/initial_velib.parquet"
    elif table_type == "arrondissement":
        table_name = external_arrondissement_table
        uri_pattern = f"gs://{bucket_name}/arrondissement.parquet"
    else:
        return "Invalid table type. Please provide either 'velib' or 'arrondissement'."
    
    ddl = f"""
    create or replace external table `{table_name}` 
    options (
        format = "PARQUET",
        uris = ["{uri_pattern}"]
    )
    """

    BQ_CLIENT.query(ddl).result()
    message = f"External table {table_name} created successfully."
    print(message)
    return message


def create_native_table(table_type: str):

    if table_type == "velib":
        external_table_name = external_velib_table
        native_table_name = native_velib_table
    elif table_type == "arrondissement":
        external_table_name = external_arrondissement_table
        native_table_name = native_arrondissement_table
    else:
        return "Invalid table type. Please provide either 'velib' or 'arrondissement'."
    
    ddl = f"""
    create or replace table `{native_table_name}` as
    select * from `{external_table_name}`
    """
    BQ_CLIENT.query(ddl).result()

    message = f"Native table {native_table_name} created successfully."

    # When load the velib data, 
    # 1) add and update a file_name column 
    # 2) update the file registry table 
    if table_type == "velib":
        add_columns_query = f"""
        alter table `{native_table_name}`
        add column file_name string
        add column ingest_time TIMESTAMP
        """
        BQ_CLIENT.query(add_columns_query).result()
        
        update_file_name_query = f"""
        update `{native_table_name}`
        set file_name = '{init_velib_filename}',
            ingest_time = CURRENT_TIMESTAMP()
        where file_name is null
        """
        BQ_CLIENT.query(update_file_name_query).result()

        init_mark_files_as_processed()

        message = f"{message} File_name created and updated, also files marked as processed."
    elif table_type == "arrondissement":
        add_columns_query = f"""
        alter table `{native_table_name}`
        add column iso_code string
        """
        BQ_CLIENT.query(add_columns_query).result()
        
        # we only have pairs arrondissement data
        update_file_name_query = f"""
        update `{native_table_name}`
        set iso_code = 'FR-75'
        where iso_code is null
        """
        BQ_CLIENT.query(update_file_name_query).result() 
    else:
        message = f"Table {table_type} is not velib or arrondissement, please check the table name."

    print(message)
    return message


def process_unprocessed_files():

    unprocessed_files = get_unprocessed_files()

    for file in unprocessed_files:

        try:
            uri_pattern = f"gs://{bucket_name}/{file}"
            # Replace the external table for each unprocessed file

            file_base = file.replace('.parquet', '')
            temp_external_table = f"{external_velib_table}_temp_{file_base}"
            load_query = f"""
            create or replace external table `{temp_external_table}`
            options (
                format = "PARQUET",
                uris = ["{uri_pattern}"]
            )
            """
            # Bug fixed: using .result()  not .result
            BQ_CLIENT.query(load_query).result()

            # Merge table
            insert_query = f"""
            insert into `{native_velib_table}` 
                (stationcode, name, is_installed, capacity, numdocksavailable, numbikesavailable, mechanical, ebike, is_renting, is_returning, duedate, coordonnees_geo, nom_arrondissement_communes, code_insee_commune, station_opening_hours, file_name, ingest_time)
            select
                stationcode, name, is_installed, capacity, numdocksavailable, numbikesavailable, mechanical, ebike, is_renting, is_returning, duedate, coordonnees_geo, nom_arrondissement_communes, code_insee_commune, station_opening_hours, '{file}' as file_name, CURRENT_TIMESTAMP() as ingest_time 
            from `{temp_external_table}`
            """
            BQ_CLIENT.query(insert_query).result()

            mark_files_as_processed(file)
            print(f"Marked file as processed: {file}")

        except Exception as e:
            mark_files_as_failed(file, str(e))
            print(f"Failed to process file {file}: {str(e)}")

    message = "All unprocessed files have been processed."
    print(message)
    return message