{{ config(
    materialized='incremental',
    unique_key=['station_code', 'update_time'],
    partition_by={
        "field": "update_time",
        "data_type": "timestamp",
        "granularity": "day"
    }
) }}

with source as (
    select
        cast(st_code.station_code as string) as station_code,
        cast(velib.numbikesavailable as int64) as numbikesavailable,
        cast(velib.numdocksavailable as int64) as numdocksavailable,
        velib.ingest_time as update_time
    from 
        {{ ref('stg_station_code') }} as st_code
    -- Only process stations we need
    inner join 
        {{source ('velib_dataset', 'velib')}} velib
    on 
        st_code.station_code = velib.stationcode
)

select
    * 
from
    source


{% if is_incremental() %}
where update_time > (
    -- Get the last updated time from the current table
    (select max(update_time) from {{ this }})
)
{% endif %}