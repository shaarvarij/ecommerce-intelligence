import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = 'ecommerce.db'

st.set_page_config(
    page_title="Revenue Intelligence",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

@st.cache_data
def query(sql):
    conn = duckdb.connect(DB_PATH)
    df   = conn.execute(sql).df()
    conn.close()
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Revenue Intelligence")
st.sidebar.markdown("E-commerce Analytics Platform")
page = st.sidebar.radio("Navigate", [
    "Executive Summary",
    "Customer Segments",
    "Revenue Forecast",
    "Churn Risk"
])
st.sidebar.markdown("---")
st.sidebar.caption("Built with DuckDB · dbt · Prophet · Streamlit")

# ── Page 1: Executive Summary ─────────────────────────────────────────────────
if page == "Executive Summary":
    st.title("Executive Summary")

    daily = query("SELECT * FROM analytics.mart_daily_revenue ORDER BY order_date")
    daily['order_date'] = pd.to_datetime(daily['order_date'])

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", daily['order_date'].min())
    with col2:
        end_date = st.date_input("To", daily['order_date'].max())

    mask    = (daily['order_date'] >= pd.Timestamp(start_date)) & \
              (daily['order_date'] <= pd.Timestamp(end_date))
    filtered = daily[mask]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue",
              f"₹{filtered['total_revenue'].sum():,.0f}")
    m2.metric("Total Orders",
              f"{filtered['total_orders'].sum():,.0f}")
    m3.metric("Avg Order Value",
              f"₹{filtered['avg_order_value'].mean():,.0f}")
    m4.metric("Unique Customers",
              f"{filtered['unique_customers'].sum():,.0f}")

    st.markdown("---")

    fig = px.line(filtered, x='order_date', y='total_revenue',
                  title='Daily Revenue',
                  labels={'order_date': 'Date', 'total_revenue': 'Revenue (₹)'})
    fig.update_traces(line_color='#1D9E75')
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        cat_rev = query("""
            SELECT p.category,
                   ROUND(SUM(o.quantity * o.unit_price), 2) AS revenue
            FROM analytics.stg_orders o
            JOIN analytics.stg_products p ON o.product_id = p.product_id
            WHERE o.is_completed = true
            GROUP BY p.category
            ORDER BY revenue DESC
        """)
        fig2 = px.bar(cat_rev, x='category', y='revenue',
                      title='Revenue by Category',
                      color='revenue',
                      color_continuous_scale='Teal')
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        channel_rev = query("""
            SELECT acquisition_channel,
                   COUNT(*) AS customers
            FROM analytics.stg_customers
            GROUP BY acquisition_channel
            ORDER BY customers DESC
        """)
        fig3 = px.pie(channel_rev, names='acquisition_channel',
                      values='customers',
                      title='Customers by Acquisition Channel')
        st.plotly_chart(fig3, use_container_width=True)

# ── Page 2: Customer Segments ─────────────────────────────────────────────────
elif page == "Customer Segments":
    st.title("Customer Segments")

    segs = query("SELECT * FROM analytics.mart_customer_segments")

    colors = {
        'Champions': '#1D9E75',
        'Loyal':     '#378ADD',
        'At Risk':   '#EF9F27',
        'Lost':      '#E24B4A',
    }

    s1, s2, s3, s4 = st.columns(4)
    for col, seg in zip([s1, s2, s3, s4],
                        ['Champions', 'Loyal', 'At Risk', 'Lost']):
        count = len(segs[segs['segment'] == seg])
        avg   = segs[segs['segment'] == seg]['total_revenue'].mean()
        col.metric(seg, f"{count} customers", f"Avg LTV ₹{avg:,.0f}")

    st.markdown("---")

    fig = px.scatter(segs, x='recency_days', y='total_revenue',
                     color='segment',
                     color_discrete_map=colors,
                     hover_data=['customer_name', 'city'],
                     title='RFM Scatter — Recency vs Revenue',
                     labels={
                         'recency_days':   'Days since last order',
                         'total_revenue':  'Total Revenue (₹)',
                     })
    st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        seg_summary = segs.groupby('segment').agg(
            customers     = ('customer_id', 'count'),
            avg_ltv       = ('total_revenue', 'mean'),
            avg_orders    = ('frequency', 'mean'),
            avg_recency   = ('recency_days', 'mean')
        ).round(1).reset_index().sort_values('avg_ltv', ascending=False)
        st.markdown("#### Segment Summary")
        st.dataframe(seg_summary, use_container_width=True, hide_index=True)

    with col_right:
        fig2 = px.bar(seg_summary, x='segment', y='customers',
                      color='segment', color_discrete_map=colors,
                      title='Customers per Segment')
        st.plotly_chart(fig2, use_container_width=True)

# ── Page 3: Revenue Forecast ──────────────────────────────────────────────────
elif page == "Revenue Forecast":
    st.title("Revenue Forecast")

    fc = query("""
        SELECT * FROM analytics.mart_revenue_forecast
        ORDER BY forecast_date
    """)
    fc['forecast_date'] = pd.to_datetime(fc['forecast_date'])

    actual   = fc[fc['record_type'] == 'actual']
    forecast = fc[fc['record_type'] == 'forecast']

    f1, f2, f3 = st.columns(3)
    f1.metric("Next 7 days (predicted)",
              f"₹{forecast.head(7)['predicted_revenue'].sum():,.0f}")
    f2.metric("Next 30 days (predicted)",
              f"₹{forecast['predicted_revenue'].sum():,.0f}")
    f3.metric("Daily avg (forecast)",
              f"₹{forecast['predicted_revenue'].mean():,.0f}")

    st.markdown("---")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=actual['forecast_date'], y=actual['predicted_revenue'],
        name='Historical', line=dict(color='#378ADD', width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=forecast['forecast_date'], y=forecast['predicted_revenue'],
        name='Forecast', line=dict(color='#1D9E75', width=2.5, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast['forecast_date'], forecast['forecast_date'][::-1]]),
        y=pd.concat([forecast['upper_bound'], forecast['lower_bound'][::-1]]),
        fill='toself', fillcolor='rgba(29,158,117,0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence interval'
    ))
    fig.update_layout(title='Revenue Forecast with Confidence Interval',
                      xaxis_title='Date', yaxis_title='Revenue (₹)')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 30-day forecast table")
    st.dataframe(forecast[['forecast_date', 'predicted_revenue',
                            'lower_bound', 'upper_bound']].reset_index(drop=True),
                 use_container_width=True, hide_index=True)

# ── Page 4: Churn Risk ────────────────────────────────────────────────────────
elif page == "Churn Risk":
    st.title("Churn Risk")

    churn = query("SELECT * FROM analytics.mart_churn_predictions ORDER BY churn_probability DESC")

    c1, c2, c3 = st.columns(3)
    c1.metric("High risk customers",
              len(churn[churn['churn_risk'] == 'High']))
    c2.metric("Medium risk customers",
              len(churn[churn['churn_risk'] == 'Medium']))
    c3.metric("Low risk customers",
              len(churn[churn['churn_risk'] == 'Low']))

    st.markdown("---")

    risk_filter = st.selectbox("Filter by risk level", ["All", "High", "Medium", "Low"])
    if risk_filter != "All":
        churn = churn[churn['churn_risk'] == risk_filter]

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.histogram(churn, x='churn_probability', nbins=30,
                           color='churn_risk',
                           color_discrete_map={
                               'High':   '#E24B4A',
                               'Medium': '#EF9F27',
                               'Low':    '#1D9E75'
                           },
                           title='Churn Probability Distribution')
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        city_churn = churn[churn['churn_risk'] == 'High'].groupby('city').size().reset_index(name='high_risk_customers')
        fig2 = px.bar(city_churn.sort_values('high_risk_customers', ascending=False),
                      x='city', y='high_risk_customers',
                      title='High Risk Customers by City',
                      color='high_risk_customers',
                      color_continuous_scale='Reds')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Customer churn risk table")
    st.dataframe(
        churn[['customer_name', 'city', 'acquisition_channel',
               'completed_orders', 'total_revenue',
               'days_since_last_order', 'churn_probability', 'churn_risk']],
        use_container_width=True, hide_index=True
    )
