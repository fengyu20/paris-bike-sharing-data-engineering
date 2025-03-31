with source as (
    select 
        c_ar as arrondissement_id,
        l_aroff as arrondissement_name,
        c_arinsee as postal_code,
        -- Covert surface column from m2 to km2
        surface / 1000000 as surface_km2,
        geom
    from 
        {{source ('velib_dataset', 'arrondissement')}}
)

select 
    *
from 
    source
