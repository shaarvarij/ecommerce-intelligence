with orders as (
    select * from {{ ref('int_orders_enriched') }}
),

customer_stats as (
    select
        customer_id,
        customer_name,
        city,
        acquisition_channel,
        signup_date,

        count(distinct order_id)                            as total_orders,
        count(distinct case
            when is_completed then order_id end)            as completed_orders,
        round(sum(case
            when is_completed then line_revenue else 0
            end), 2)                                        as total_revenue,
        round(avg(case
            when is_completed then line_revenue end), 2)    as avg_order_value,
        min(order_date)                                     as first_order_date,
        max(order_date)                                     as last_order_date,
        max(order_date)                                     as most_recent_order
    from orders
    group by
        customer_id, customer_name, city,
        acquisition_channel, signup_date
)

select * from customer_stats
