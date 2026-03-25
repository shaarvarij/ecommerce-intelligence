with source as (
    select * from raw.products
),

cleaned as (
    select
        product_id,
        product_name,
        category,
        cost_price,
        list_price,
        round(list_price - cost_price, 2)           as gross_margin,
        round((list_price - cost_price)
              / list_price * 100, 2)                as margin_pct
    from source
    where product_id is not null
      and list_price > cost_price
)

select * from cleaned
