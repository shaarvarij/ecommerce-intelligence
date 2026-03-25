with orders as (
    select * from {{ ref('int_orders_enriched') }}
    where is_completed = true
),

daily as (
    select
        order_date,
        count(distinct order_id)        as total_orders,
        count(distinct customer_id)     as unique_customers,
        round(sum(line_revenue), 2)     as total_revenue,
        round(avg(line_revenue), 2)     as avg_order_value
    from orders
    group by order_date
)

select * from daily
order by order_date
