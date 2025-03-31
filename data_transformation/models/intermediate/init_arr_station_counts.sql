with aggregated_by_arrondissement as (
    select 
        arrondissement_id,
        count(distinct station_code) as station_count
    from 
        {{ ref('int_station_arrondissement') }}
    group by
        arrondissement_id
)

select * from aggregated_by_arrondissement