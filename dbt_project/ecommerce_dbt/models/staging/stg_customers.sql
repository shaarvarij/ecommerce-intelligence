with source as (
    select * from raw.customers
),

cleaned as (
    select
        customer_id,
        name                                as customer_name,
        lower(email)                        as email,
        city,
        cast(signup_date as date)           as signup_date,
        acquisition_channel
    from source
    where customer_id is not null
      and email is not null
)

select * from cleaned
