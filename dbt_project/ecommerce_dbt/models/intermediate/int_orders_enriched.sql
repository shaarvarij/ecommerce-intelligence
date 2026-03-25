with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

enriched as (
    select
        o.order_id,
        o.order_date,
        o.status,
        o.is_completed,
        o.quantity,
        o.unit_price,
        o.line_revenue,

        c.customer_id,
        c.customer_name,
        c.city,
        c.acquisition_channel,
        c.signup_date,

        p.product_id,
        p.product_name,
        p.category,
        p.cost_price,
        p.margin_pct
    from orders o
    left join customers c on o.customer_id = c.customer_id
    left join products  p on o.product_id  = p.product_id
)

select * from enriched
