-- static: mart_arr_station_density


with arrondissement_station_density as (
    select 
        agg_arr.arrondissement_id,
        arr_info.arrondissement_name,
        agg_arr.station_count,
        arr_info.surface_km2,
        round(safe_divide(agg_arr.station_count, arr_info.surface_km2),2) as station_density,
        arr_info.geom
    from 
        {{ ref('int_station_arrondissement') }} as arr_info
    join 
        {{ ref('init_arr_station_counts')}} as agg_arr
      on arr_info.arrondissement_id = agg_arr.arrondissement_id
)

select
    *
from
    arrondissement_station_density
order by  
    arrondissement_id