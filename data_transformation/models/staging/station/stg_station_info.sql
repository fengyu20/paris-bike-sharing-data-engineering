
with source as (
    select 
        st_code.station_code,
        name as station_name,
        coordonnees_geo as geo_location,
        code_insee_commune as postal_code,
        -- location for looker studio geo map rendering
        concat(
            cast(ST_Y(coordonnees_geo) as string),
            ',', 
            cast(ST_X(coordonnees_geo) AS string)
        ) AS location
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
