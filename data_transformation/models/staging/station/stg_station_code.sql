{{
    config(
        materialized='incremental',
        unique_key='station_code'
    )
}}

with source as (
    select 
        distinct stationcode as station_code
    from 
        {{source ('velib_dataset', 'velib')}}
    where 
        -- Only select the stations that are installed and also located in Paris
        is_installed = "OUI"
        and nom_arrondissement_communes = "Paris"
    group by
        stationcode
    having 
        -- Only include stations with duedates later than January 1, 2025.
        min(duedate) > "2025-01-01 00:00:00 UTC"
        
)

select 
    *
from 
    source


{% if is_incremental() %}
  where station_code not in (select station_code from {{ this }})
{% endif %}