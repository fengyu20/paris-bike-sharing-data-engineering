This document was written when I first started working on the project. I tried to outline the main steps and logic before beginning the actual coding process.

It served as a skeleton for my work and helped me avoid getting lost in technical details.

Although additional elements have been added to the project over time, this document does not include all the details or subsequent changes I have made. For a detailed description of the final project, please refer to [README](../README.md).

---

## 0. Preconfiguration

- **Terraform Setup:**  
  - Use Terraform to provision all necessary Google Cloud resources:
    - **Cloud Storage Bucket(s):** For storing raw Parquet snapshots and other file-based data.

- **Airflow Environment:**  
  - Use a local Airflow setup during the development phase.
  - Consider using **Cloud Composer** for consistent scheduling; otherwise, the local host must remain running to fetch datasets.

---

## 1. Data Sources

### a. Velib Parquet Data
- **Source:**  
  Use the URL:  
  `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/exports/parquet?lang=fr&timezone=Europe%2FBerlin`  
  This returns a Parquet file named `velib-disponibilite-en-temps-reel.parquet`.

- **Processing:**  
  In each ingestion run, rename the file to `velib_{current_paris_timestamp}.parquet`, then upload it to Cloud Storage.

### b. District Information Data
- **Source:**  
  Use the URL:  
  `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/parquet?lang=fr&timezone=Europe%2FBerlin`  
  This returns a Parquet file containing district boundaries and metadata (e.g., `n_sq_ar`, `c_ar`, `l_ar`, `surface`, `geom_x_y`, and `geom`).

- **Usage:**  
  1. Load only once during the initialization step. Save the Parquet file in Cloud Storage and create external and native tables in BigQuery.
  2. In dbt transformations, use BigQuery’s GIS functions (e.g., `ST_CONTAINS`, `ST_WITHIN`) to add district information to stations.

---

## 2. Data Ingestion (via Airflow)

### 2.1 Initialization DAG - Downloading/Uploading Data & Creating Tables

- **Purpose:** Ensure new users have all necessary data before running downstream pipelines.

- **Tasks:**
  - Request Velib and district Parquet files from their respective sources.
  - Rename the Velib file uniquely (e.g., `velib_{current_paris_timestamp}.parquet`) and upload both files to Cloud Storage.
  - Create external and native tables for Velib data pointing to Cloud Storage files.
  - Create external and native tables for district information.
  - Create a file registry table (internal) to track processed files.

### 2.2 Hourly Ingestion DAG
- **Purpose:** Fetch hourly snapshots of Vélib data.

- **Tasks:**
  - Request Velib Parquet file.
  - Rename the file using Paris local time format (`velib_{current_paris_timestamp}.parquet`).
  - Upload the renamed file to Cloud Storage.
  - Load the Parquet file into BigQuery.

### 2.3 Daily dbt Transformation DAG
- **Purpose:** Trigger daily dbt transformations.

---

## 3. Data Transformation (using dbt)

### dbt Models and Logic

1. **Source Tables:** Defined in `source.yml`.
   - Velib Status Table (updated daily)
   - District Table (created during initialization)

2. **Staging Models:** Defined in the staging folder, referencing source tables. Rename columns, perform light cleaning, and data type transformations.
   - `station_status.sql` – Clean and standardize dynamic data (e.g., available bikes).
   - `station_information.sql` – Clean and standardize static data (e.g., locations).
   - `station_codes.sql` – Incremental model extracting unique station codes, accounting for new stations without district info.
   - `district_info.sql` – District information (names, areas, boundaries).

3. **Intermediate Models:**
   - `station_district_info.sql` – Enriched station codes with district data, joined using BigQuery spatial functions.
   - `station_status.sql` – Initial table containing hourly snapshots.

4. **Mart Models:**
   - `station_volatility.sql` – Calculates standard deviation of bike availability over the last 7 days.
   - `district_bike_density.sql` – Computes bike density (bikes per km²) by joining dynamic status with static station and district area information.

---

## 4. Data Visualization

- **Tools:**  
  Use Looker Studio to create dashboards with the following visualizations:

  1. **Volatility Dashboard Tile:**  
     "Which Vélib station has the highest volatility in bike availability on a given day?"

  2. **Bike Density Dashboard Tile:**  
     "Which Paris district has the highest parked bike density (bikes per km²) over the past day?"

  3. **Station Density Dashboard Tile:**  
     "Which Paris district has the highest station density (stations per km²)?"

