import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Revenue Intelligence",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

DATA_DIR = 'data/marts'

@st.cache_data
def load(filename):
    return pd.read_csv(f'{DATA_DIR}/{filename}')

daily    = load('mart_daily_revenue.csv')
segments = load('mart_customer_segments.csv')
forecast = load('mart_revenue_forecast.csv')
churn    = load('mart_churn_predictions.csv')
products = load('mart_product_performance.csv')
customers= load('stg_customers.csv')
orders   = load('stg_orders.csv')
stg_prod = load('stg_products.csv')

daily['order_date']       = pd.to_datetime(daily['order_date'])
forecast['forecast_date'] = pd.to_datetime(forecast['forecast_date'])

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

if page == "Executive Summary":
    st.title("Executive Summary")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", daily['order_date'].min())
    with col2:
        end_date = st.date_input("To", daily['order_date'].max())

    mask     = (daily['order_date'] >= pd.Timestamp(start_date)) & \
               (daily['order_date'] <= pd.Timestamp(end_date))
    filtered = daily[mask]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue",      f"₹{filtered['total_revenue'].sum():,.0f}")
    m2.metric("Total Orders",       f"{filtered['total_orders'].sum():,.0f}")
    m3.metric("Avg Order Value",    f"₹{filtered['avg_order_value'].mean():,.0f}")
    m4.metric("Unique Customers",   f"{filtered['unique_customers'].sum():,.0f}")

    st.markdown("---")

    fig = px.line(filtered, x='order_date', y='total_revenue',
                  title='Daily Revenue',
                  labels={'order_date':'Date','total_revenue':'Revenue (₹)'})
    fig.update_traces(line_color='#1D9E75')
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        cat_rev = (orders[orders['is_completed']==True]
                   .merge(stg_prod[['product_id','category']], on='product_id')
                   .groupby('category')['line_revenue'].sum()
                   .reset_index()
                   .rename(columns={'line_revenue':'revenue'})
                   .sort_values('revenue', ascending=False))
        fig2 = px.bar(cat_rev, x='category', y='revenue',
                      title='Revenue by Category',
                      color='revenue', color_continuous_scale='Teal')
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        ch = customers.groupby('acquisition_channel').size().reset_index(name='customers')
        fig3 = px.pie(ch, names='acquisition_channel', values='customers',
                      title='Customers by Acquisition Channel')
        st.plotly_chart(fig3, use_container_width=True)

elif page == "Customer Segments":
    st.title("Customer Segments")

    colors = {
        'Champions': '#1D9E75',
        'Loyal':     '#378ADD',
        'At Risk':   '#EF9F27',
        'Lost':      '#E24B4A',
    }

    s1, s2, s3, s4 = st.columns(4)
    for col, seg in zip([s1, s2, s3, s4],
                        ['Champions', 'Loyal', 'At Risk', 'Lost']):
        subset = segments[segments['segment'] == seg]
        count  = len(subset)
        avg    = subset['total_revenue'].mean() if count > 0 else 0
        col.metric(seg, f"{count} customers", f"Avg LTV ₹{avg:,.0f}")

    st.markdown("---")

    fig = px.scatter(segments, x='recency_days', y='total_revenue',
                     color='segment', color_discrete_map=colors,
                     hover_data=['customer_name', 'city'],
                     title='RFM Scatter — Recency vs Revenue',
                     labels={'recency_days':'Days since last order',
                             'total_revenue':'Total Revenue (₹)'})
    st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        seg_summary = segments.groupby('segment').agg(
            customers   =('customer_id','count'),
            avg_ltv     =('total_revenue','mean'),
            avg_orders  =('frequency','mean'),
            avg_recency =('recency_days','mean')
        ).round(1).reset_index().sort_values('avg_ltv', ascending=False)
        st.markdown("#### Segment Summary")
        st.dataframe(seg_summary, use_container_width=True, hide_index=True)

    with col_right:
        fig2 = px.bar(seg_summary, x='segment', y='customers',
                      color='segment', color_discrete_map=colors,
                      title='Customers per Segment')
        st.plotly_chart(fig2, use_container_width=True)

elif page == "Revenue Forecast":
    st.title("Revenue Forecast")

    actual   = forecast[forecast['record_type'] == 'actual']
    fc_only  = forecast[forecast['record_type'] == 'forecast']

    f1, f2, f3 = st.columns(3)
    f1.metric("Next 7 days (predicted)",
              f"₹{fc_only.head(7)['predicted_revenue'].sum():,.0f}")
    f2.metric("Next 30 days (predicted)",
              f"₹{fc_only['predicted_revenue'].sum():,.0f}")
    f3.metric("Daily avg (forecast)",
              f"₹{fc_only['predicted_revenue'].mean():,.0f}")

    st.markdown("---")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=actual['forecast_date'], y=actual['predicted_revenue'],
        name='Historical', line=dict(color='#378ADD', width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=fc_only['forecast_date'], y=fc_only['predicted_revenue'],
        name='Forecast', line=dict(color='#1D9E75', width=2.5, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([fc_only['forecast_date'],
                     fc_only['forecast_date'][::-1]]),
        y=pd.concat([fc_only['upper_bound'],
                     fc_only['lower_bound'][::-1]]),
        fill='toself', fillcolor='rgba(29,158,117,0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence interval'
    ))
    fig.update_layout(title='Revenue Forecast with Confidence Interval',
                      xaxis_title='Date', yaxis_title='Revenue (₹)')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 30-day forecast table")
    st.dataframe(fc_only[['forecast_date','predicted_revenue',
                           'lower_bound','upper_bound']].reset_index(drop=True),
                 use_container_width=True, hide_index=True)

elif page == "Churn Risk":
    st.title("Churn Risk")

    c1, c2, c3 = st.columns(3)
    c1.metric("High risk",   len(churn[churn['churn_risk']=='High']))
    c2.metric("Medium risk", len(churn[churn['churn_risk']=='Medium']))
    c3.metric("Low risk",    len(churn[churn['churn_risk']=='Low']))

    st.markdown("---")

    risk_filter = st.selectbox("Filter by risk level", ["All","High","Medium","Low"])
    filtered_churn = churn if risk_filter == "All" else churn[churn['churn_risk']==risk_filter]

    col_l, col_r = st.columns(2)
    with col_l:
        fig = px.histogram(filtered_churn, x='churn_probability', nbins=30,
                           color='churn_risk',
                           color_discrete_map={
                               'High':'#E24B4A','Medium':'#EF9F27','Low':'#1D9E75'
                           },
                           title='Churn Probability Distribution')
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        city_churn = (churn[churn['churn_risk']=='High']
                      .groupby('city').size()
                      .reset_index(name='high_risk_customers')
                      .sort_values('high_risk_customers', ascending=False))
        fig2 = px.bar(city_churn, x='city', y='high_risk_customers',
                      title='High Risk Customers by City',
                      color='high_risk_customers',
                      color_continuous_scale='Reds')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Customer churn risk table")
    st.dataframe(
        filtered_churn[['customer_name','city','acquisition_channel',
                        'completed_orders','total_revenue',
                        'days_since_last_order','churn_probability','churn_risk']],
        use_container_width=True, hide_index=True
    )
