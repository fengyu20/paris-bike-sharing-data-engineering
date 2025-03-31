# Paris Public Bike-Sharing(Velib) Data Engineering Project

This project builds a scalable data engineering pipeline that ingests data from Paris's Vélib' bike-sharing system, processes and transforms the data, and finally visualizes it to provide insights for understanding public biking in Paris.

## Table of Contents

- [High-Level Workflow & Architecture](#high-level-workflow--architecture)
  - [Project Structure](#project-structure)
  - [Tools Overview](#tools-overview)
- [Project Architecture Details](#project-architecture-details)
  - [1. Problem Description](#1-problem-description)
  - [2. Cloud Infrastructure & IaC](#2-cloud-infrastructure--iac)
  - [3. Data Ingestion (Batch Processing)](#3-data-ingestion-batch-processing)
  - [4. Data Warehouse Design](#4-data-warehouse-design)
  - [5. Transformations with dbt](#5-transformations-with-dbt)
  - [6. Dashboard](#6-dashboard)
  - [7. Reproducibility](#7-reproducibility)
- [Hands-on: How to Reproduce This Project](#hands-on-how-to-reproduce-this-project)
  - [Understand Data Sources](#understand-data-sources)
    - [Velib Station Status](#velib-station-status)
    - [Arrondissement Data](#arrondissement-data)
  - [Step-by-Step Instructions](#step-by-step-instructions)
    - [Preparation: Git Clone](#preparation-git-clone)
    - [A. Cloud Infrastructure Using Terraform](#a-cloud-infrastructure-using-terraform)
    - [B. Data Ingestion Using Airflow](#b-data-ingestion-using-airflow)
    - [C. Data Transformation Using dbt Core](#c-data-transformation-using-dbt-core)
    - [D: Optional: Cloud Composer + dbt Cloud](#d-optional-cloud-composer--dbt-cloud)
- [Future Plans & Takeaways](#future-plans--takeaways)
  - [Future Plans](#future-plans)
  - [Takeaways for the Next Project](#takeaways-for-the-next-project)

## High-Level Workflow & Architecture

### Project Structure 

```
velib-data-engineering-project/
├── cloud_infrastructure/       # Terraform configuration for GCP resources
│   ├── main.tf                # Main Terraform configuration
│   ├── variables.tf           # Variable definitions
│   └── terraform.tfvars       # Variable values
│
├── data_ingestion/             # Airflow DAGs and utilities
│   ├── dags/                  # Airflow DAG definitions
│   │   ├── init_ingestion_velib_arr_dag.py    # Initial data load
│   │   ├── hourly_ingestion_velib_dag.py      # Hourly Vélib data updates and loads
│   │   └── daily_dbt_transformation_dag.py      # DBT transformation trigger
│   └── utils/                 # Shared utility functions
│       ├── config.py          # Configuration settings
│       ├── gcp_big_query.py   # BigQuery operations
│       ├── gcp_cloud_storage.py  # GCS operations
│       └── velib_file_registry.py # Tracking the status of downloaded Vélib files 
│
├── data_transformation/        # dbt project for data transformations
│   ├── models/
│   │   ├── staging/           # Initial data cleaning
│   │   ├── intermediate/      # Intermediate calculations
│   │   └── marts/            # Final analytical tables
│   ├── dbt_project.yml        # dbt project configuration
│   └── profiles.yml           # dbt connection profiles
│
├── requirements.txt           # Python dependencies
└── README.md                  # This combined documentation
```

### Tools Overview

![pic](/docs/diagram.jpg)

Main technical tools used:
1. **Google Cloud:** 
   - **Cloud Storage:** the data lake used to store original data pulled from Paris opendata websites.
   - **BigQuery:** the data warehouse into which the original data is extracted.
   - **Looker + Google Colab:** data visualization.
   - **(Optional - Airflow cloud version) Cloud Composer:** the Airflow environment running on Google Cloud.
2. **Terraform:** Infrastructure as Code.
   - Manages the Google Cloud infrastructure.
3. **Airflow:** Data ingestion.
   - Orchestrates the data ingestion part (original data → data lake → data warehouse).
   - Schedules the dbt core to run data transformation.
4. **dbt:** Data transformation.
   - Loads data from the original source and transforms it to what we need.

> [!NOTE]  
> This project provides two options for running Airflow. One is the **cloud version**, which uses Cloud Composer to run Airflow and dbt Cloud to schedule the jobs. The other is the **local environment version**, which is responsible for also orchestrating dbt core (dbt open-source version).


## Project Architecture Details

### 1. Problem Description

This project addresses the challenge of collecting, processing, and analyzing real-time data from Paris's Vélib' bike-sharing system. It solves several specific problems:
- **Data Collection:** Capturing hourly snapshots of Velib bike station data.
- **Geospatial Analysis:** Matching bike stations to arrondissements.
- **Station Distribution:** Understanding the station density in each arrondissement.
- **Volatility Measurement:** Identifying stations with the highest variations in bike availability.


### 2. Cloud Infrastructure & IaC

The entire infrastructure is deployed on Google Cloud Platform using Terraform for Infrastructure as Code (IaC):

All GCP resources (Cloud Storage buckets, BigQuery datasets, Cloud Composer for Airflow) are defined in Terraform files located in `/cloud_infrastructure/main.tf`.


> [!TIP]
> Check out [this article](https://github.com/fengyu20/data-engineering-zoomcamp-2025/tree/main/terraform) to learn more about Terraform.

### 3. Data Ingestion (Batch Processing)

Data ingestion is managed via Apache Airflow using multiple DAGs:

![airflow](/docs/airflow.png)

- **Initialization DAG (`init_ingestion_velib_arr_dag.py`):**
  - Downloads and uploads both arrondissement boundary data and initial Vélib data.
  - Creates external tables in BigQuery and establishes a file registry table.
  
- **Hourly Ingestion DAG (`hourly_ingestion_velib_dag.py`):**
  - Fetches new snapshots hourly from the Paris Open Data API.
  - Uploads data to Google Cloud Storage.
  - Updates the file registry and processes files into BigQuery tables.

- **Daily Transformation DAG(`daily_dbt_transformation_dag.py`):**
  - Triggers the dbt run when using the Airflow local environment and dbt core version.



### 4. Data Warehouse Design

BigQuery serves as the centralized data warehouse, employing optimized design strategies.

- **Native Table:**  
  After creating the external tables to load the parquet files, we then create the native table to enhance query performance.

- **Incremental Loading:**  
  Only new data is processed through incremental loading patterns, ensuring no duplicate entries.

- **Partitioning Strategy:**  
  When materializing new tables in BigQuery (the materialization step is performed through dbt and achieved in BigQuery), mart tables are partitioned by time (e.g., `last_record_time`) to enhance query performance.
  
  ```sql
  {{ config(
      materialized='incremental',
      unique_key=['station_code', 'last_record_time'],
      partition_by={
          "field": "last_record_time",
          "data_type": "timestamp",
          "granularity": "day"
      }
  ) }}
  ```

### 5. Transformations with dbt

The project uses dbt to perform modular data transformations, following [the best practice](https://github.com/fengyu20/data-engineering-zoomcamp-2025/tree/main/dbt#1-dbt-model):

![pic](/docs/dbt.png)

- **Staging Models (`/data_transformation/models/staging/`):**
  - Filter, clean and standardize raw data.

- **Intermediate Models (`/data_transformation/models/intermediate/`):**
  - Join datasets and add contextual enrichment (e.g., matching stations with arrondissements).

- **Mart Models (`/data_transformation/models/marts/`):**
  - Create final, analytics-ready views.

> [!NOTE]  
> Depending on where you run Airflow, there are two options to trigger the dbt transformation.  
> **1. Cloud version:** When using Cloud Composer, use dbt Cloud for scheduling the jobs.  
> **2. Local version:** Airflow also automates the daily execution of the entire dbt project, ensuring transformations occur after data ingestion.


> [!TIP]
> Check out [this article](https://github.com/fengyu20/data-engineering-zoomcamp-2025/tree/main/dbt) to learn more about dbt.

### 6. Dashboard

The project creates the following dashboards:

- **Arrondissement Station Density Dashboard:** created using [Colab](/data_visualization/arr_station_density.ipynb).
  - **Data Source:** `mart_arr_station_density` model.
  - **Metrics:** Stations per km²  
  ![pic](/docs/arr_station_density.png)

- **Station Bike Status Dashboard:** created using Looker Studio.
  - **Data Source:** `mart_station_status` model.
  - **Fluctuation Tile:** Shows the standard deviation of bike availability, min/max bikes.
    - ![pic](/docs/station_fluctuation.png)
  - **Heatmap Tile:** Shows the number of bikes at each station; you can use the filter to get a snapshot of a certain time's bike distribution.
    - ![pic](/docs/bike_heatmap.png)
  - **Time Trend by Station:** Understand how bike availability changes over time by selecting a certain station.
    - ![pic](/docs/station_trend.png)
  - **Time Trend by Arrondissement:** Understand how bike availability changes over time for different arrondissements.
    - ![pic](/docs/arr_bike_trend.png)
  - **Arrondissement Bike Availability and Density Over Time:** Shows how densely bikes are distributed with how many bikes are available overall across different arrondissements.
    - ![pic](/docs/arr_bike_density.png)

### 7. Reproducibility

The project is designed for easy reproduction and onboarding. Follow the hands-on section below to reproduce the project.

## Hands-on: How to Reproduce This Project


### Understand Data Sources

> [!NOTE]  
> License: These two datasets are made available under the [Open Database License](http://opendatacommons.org/licenses/odbl/1.0/). Any rights in individual contents of the database are licensed under the [Database Contents License](http://opendatacommons.org/licenses/dbcl/1.0/).

### Velib Station Status

In this project, we download all station information hourly into a Parquet file.

Source: [Paris Open Data – Vélib' Availability in Real-Time](https://opendata.paris.fr/explore/dataset/velib-disponibilite-en-temps-reel/dataviz)

  
### Arrondissement Data

This dataset provides arrondissement names, postal codes, surface areas, and geographic boundaries.

Source: [Paris Arrondissements Data](https://opendata.paris.fr/explore/dataset/arrondissements)  
 

### Step-by-Step Instructions

#### Preparation: Git Clone

Clone the entire repository into your local environment.

```bash
git clone <repository-url>
```

#### A. Cloud Infrastructure Using Terraform

##### 1. Install Terraform

On macOS:
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```
For other systems, refer to the [Terraform documentation](https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/install-cli).

##### 2. Build Infrastructure

1. **Navigate:** Go to the `cloud_infrastructure` directory.
2. **Configure:** Update `terraform.tfvars` with your GCP project ID and region.
3. **Authenticate:**  
   ```bash
   gcloud auth application-default login
   ```
4. **Initialize Terraform:**  
   ```bash
   terraform init
   ```
   Ensure you see the message: *Terraform has been successfully initialized!*.
5. **Apply Configuration:**  
   ```bash
   terraform apply
   ```
   Type `yes` when prompted to provision resources. Rerun `terraform apply` after modifying configuration files.

> [!NOTE]    
> - **Cloud Composer Usage**: I commented out the Cloud Composer section because you can also run Airflow locally. Cloud Composer can cost at least 10 euros per day. You can uncomment it if you want to try the Cloud Composer environment, which may take around 20 minutes to fully launch. Custom environment variables are used. See [this doc](https://cloud.google.com/composer/docs/composer-3/create-environments#overrides-env-vars) for details.

##### 3. Destroy Infrastructure

To remove resources:
```bash
terraform destroy
```
This terminates and deletes all resources managed by Terraform.

> [!IMPORTANT]  
> If you use Cloud Composer, `terraform destroy` won’t be able to destroy the Google Cloud Storage bucket for the DAG folder; you need to manually delete it when you don’t need it anymore.


#### B. Data Ingestion Using Airflow

1. **Create a Virtual Environment:**
   ```bash
   python3.11 -m venv myenv
   source myenv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install Airflow:**
   ```bash
   bash <<'EOF'
   AIRFLOW_VERSION=2.10.5
   PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
   CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

   pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
   EOF
   ```
   For more details, refer to [Airflow’s documentation](https://airflow.apache.org/docs/apache-airflow/stable/start.html).

3. **Install Google Provider for Airflow:**
   ```bash
   pip install apache-airflow-providers-google
   ```
   Note: In development, we use [ADC credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc) configured by Terraform (`gcloud auth application-default login`), so additional service account configuration is not needed.

4. **Start Airflow:**
   ```bash
   airflow standalone
   ```
   Access the Airflow UI at `localhost:8080` using the provided credentials (e.g., username: admin, password: your_generated_password).

5. **Test GCP Connection by Running a Test Task:**
   - Update `~/airflow/airflow.cfg` to set the `dags_folder` to `$(pwd)/data_ingestion`.
   - Confirm the update using `airflow config get-value core dags_folder`.
   - Trigger the first DAG in the initial DAG:
     ```bash
     airflow tasks test init_data_dag create_file_registry_table
     ```
     This will create the first table in your BigQuery dataset.



#### C. Data Transformation Using dbt Core

For the local environment, choose dbt Core as it can be easily integrated with Airflow to trigger the dbt project.

1. **Install dbt:**
   In the same virtual env, install dbt:
   ```bash
   source myenv/bin/activate
   pip install dbt-core dbt-bigquery
   ```
2. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth application-default login \
   https://www.googleapis.com/auth/drive.readonly,\
   https://www.googleapis.com/auth/iam.test
   ```
3. **Run the Project:**
   Simply execute:
   ```bash
   dbt build
   ```
   to run SQL queries in BigQuery.


#### D: Optional: Cloud Composer + dbt Cloud

> [!NOTE]  
> Assume you have created the Cloud Composer environment using Terraform. If not, uncomment the relevant section and use `terraform apply` to create it.

##### Cloud Composer
1. **Upload DAGs to Composer:**
   ```bash
   gcloud composer environments storage dags import \
       --environment <composer_environment> \
       --location <location> \
       --source="data_ingestion/dags/*"
   ```
   - After uploading the files, it will take some time for them to appear in the Airflow UI.
   - You can get the Airflow UI address and the bucket created by Cloud Composer using Terraform output variables. For more information, check [this section](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/composer_environment.html#attributes-reference).

2. **Troubleshooting:**  
   When you upload the DAG files to the bucket, you might encounter some import errors. Check [this doc](https://cloud.google.com/composer/docs/composer-3/known-issues#airflow_ui_might_sometimes_not_re-load_a_plugin_once_it_is_changed) for troubleshooting.
   ```bash
   gcloud beta composer environments restart-web-server ENVIRONMENT_NAME --location=LOCATION
   ```
   An easy way to reload the environment is to add a dummy variable with a value of False in the environment variables. More details can be found [here](https://stackoverflow.com/a/55510638).

##### dbt Cloud

1. **Setup:**  
   Grant dbt Cloud access to your Google BigQuery dataset ([BigQuery Access Guide](https://docs.getdbt.com/guides/bigquery)) and connect your GitHub repository ([GitHub Connect Guide](https://docs.getdbt.com/docs/cloud/git/connect-github)).
2. **Configuration:**
   Set the BigQuery dataset name as `velib_dataset` and the GitHub folder as `data_transformation`.
3. **Schedule Jobs:**
   Check [this section](https://github.com/fengyu20/data-engineering-zoomcamp-2025/tree/main/dbt#triggering-jobs-in-dbt) to see the daily job configuration.  

   ![pic](/docs/dbt_run.png)



## Future Plans & Takeaways

### Future Plans
1. **Additional Data Resources:**  
   Integrate more datasets to further analyze Paris's biking data.
2. **Portability:**  
   Use Docker and Kubernetes for easier coordination of modules and quick startup.
3. **Automation & Data Quality:**  
   Add a CI/CD pipeline to allow more automation in the pipeline. For example, in the context of Cloud Composer, when detecting changes in the DAGs folder via GitHub, trigger an upload action to the Cloud Storage DAGs path.
4. **Enhanced Error Handling:**  
   Improve retry logic and alerting for data ingestion failures. For example, sometimes there is no data in the downloaded parquet files, so a retry for downloading is needed.
5. **dbt Transformation Structure:**  
   Even though we try to implement the best practices, future enhancements are needed to improve the lineage.

### Takeaways for the Next Project
1. **Start with design documentation**: Write down your thoughts and have at least a [design document](/docs/initial_design.md) to guide you through development; this can save time and help avoid getting lost in the details.
2. **Test the transformation logic incrementally**: First, upload parquet files to Cloud Storage and validate the transformation logic directly in BigQuery to ensure it produces the expected results. Once it makes sense there, implement it in dbt. Finally, if the whole workflow is working as intended, integrate and orchestrate it using Airflow.

