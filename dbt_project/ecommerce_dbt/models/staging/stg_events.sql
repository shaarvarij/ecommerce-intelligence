with source as (
    select * from raw.events
),

cleaned as (
    select
        event_id,
        customer_id,
        product_id,
        event_type,
        cast(event_time as timestamp)   as event_time,
        cast(event_time as date)        as event_date,
        page,
        session_id
    from source
    where event_id is not null
)

select * from cleaned
