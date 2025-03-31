from airflow.models import Variable

# Get the project_id, bucket_name, and region from Airflow Variables
# Project_id is the reserved word
project = Variable.get("project")
bucket_name = Variable.get("bucket_name")
region = Variable.get("region")
dataset_name = Variable.get("dataset_name")

# Define the file name
arrondissement_filename = "arrondissement.parquet"
init_velib_filename = "initial_velib.parquet"

# Define the table name and path
external_velib_table = f"{project}.{dataset_name}.external_velib"
native_velib_table = f"{project}.{dataset_name}.velib"
registry_table = f"{project}.{dataset_name}.file_registry"
external_arrondissement_table = f"{project}.{dataset_name}.external_arrondissement"
native_arrondissement_table = f"{project}.{dataset_name}.arrondissement"

# List of URLs for data sources
velib_url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/parquet?lang=fr&timezone=Europe%2FBerlin"
arrondissement_url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/parquet?lang=fr&timezone=Europe%2FBerlin"
