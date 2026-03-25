with source as (
    select * from raw.orders
),

cleaned as (
    select
        order_id,
        customer_id,
        product_id,
        cast(order_date as date)          as order_date,
        quantity,
        unit_price,
        round(quantity * unit_price, 2)   as line_revenue,
        status,
        case
            when status = 'completed' then true
            else false
        end                               as is_completed
    from source
    where order_id is not null
      and customer_id is not null
      and quantity > 0
      and unit_price > 0
)

select * from cleaned
