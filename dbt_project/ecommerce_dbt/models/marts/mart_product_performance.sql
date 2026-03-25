with orders as (
    select * from {{ ref('int_orders_enriched') }}
    where is_completed = true
)

select
    product_id,
    product_name,
    category,
    margin_pct,
    count(distinct order_id)        as total_orders,
    sum(quantity)                   as units_sold,
    round(sum(line_revenue), 2)     as total_revenue,
    round(avg(line_revenue), 2)     as avg_order_value
from orders
group by product_id, product_name, category, margin_pct
order by total_revenue desc
