
with source as (
    select 
        st_code.station_code,
        st_info.station_name,
        st_info.location,
        arr.arrondissement_id,
        arr.arrondissement_name,
        arr.geom,
        arr.surface_km2
    from 
        {{ref ('stg_station_code')}} as st_code
    left join
        {{ref ('stg_station_info')}} as st_info
        on st_code.station_code = st_info.station_code
    join 
        {{ref ('stg_arrondissement_info')}} as arr
        on st_within(
            st_info.geo_location,
            arr.geom
        )
)

select 
    *
from 
    source
