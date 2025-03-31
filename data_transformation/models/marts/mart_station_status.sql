{{ config(
    materialized='incremental',
    unique_key=['station_code', 'last_record_time'],
    partition_by={
        "field": "last_record_time",
        "data_type": "timestamp",
        "granularity": "day"
    }
) }}

-- unique station code
with stations as (
    select station_code from {{ ref('int_station_arrondissement') }}
),
-- create time grid array 
time_grid as (
    select
        t as normalized_time
    -- unnest: flatten the array -> time become a seperate row
    -- doc: https://cloud.google.com/bigquery/docs/arrays#flattening_arrays
    from unnest(
        -- generate_timestamp_array: create an array of timestamps with start, end, interval
        -- doc: https://cloud.google.com/bigquery/docs/reference/standard-sql/array_functions#generate_timestamp_array
        generate_timestamp_array(
            -- timestamp_sub: get the time period, last day's hour - today's hour
            timestamp_sub(timestamp_trunc(current_timestamp(), hour), interval 1 day),
            -- timestamp_trunc: return the nearest hour
            timestamp_trunc(current_timestamp(), hour),
            interval 1 hour
        )
    ) as t
),
station_time_grid as (
    select
        s.station_code,
        tg.normalized_time
    from 
        stations s
    -- one to many: every station have mutliple normalized time stamps
    cross join 
        time_grid tg
),
joined as (
    select
        stg.station_code,
        stg.normalized_time,
        src.numdocksavailable,
        src.numbikesavailable,
        src.update_time,
        -- create the row number for each station code x normalized time
        -- doc: https://cloud.google.com/bigquery/docs/reference/standard-sql/numbering_functions#row_number
        row_number() over (
            partition by stg.station_code, stg.normalized_time 
            order by src.update_time desc
        ) as rn
    from 
        station_time_grid stg
    left join 
        {{ ref('stg_station_status') }} src  
      on 
        src.station_code = stg.station_code
      and 
        src.update_time <= stg.normalized_time
), 
source as (
    select
        station_code,
        normalized_time,
        numdocksavailable,
        numbikesavailable,
        update_time as last_record_time
    from 
        joined
    where 
        -- only get the lastest update for the station
        rn = 1
        -- no need for order by in partitioned table
)

select 
    source.*,
    static_info.station_name,
    static_info.arrondissement_name,
    static_info.location,
    static_info.geom,
    static_info.surface_km2
from 
    source 
join 
    {{ ref('int_station_arrondissement') }} as static_info
    on source.station_code = static_info.station_code
    