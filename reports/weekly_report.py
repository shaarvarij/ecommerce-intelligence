import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
import os

DB_PATH     = 'ecommerce.db'
REPORTS_DIR = 'reports'
os.makedirs(REPORTS_DIR, exist_ok=True)

conn = duckdb.connect(DB_PATH)

# ── Pull data ─────────────────────────────────────────────────────────────────
daily = conn.execute("""
    SELECT * FROM analytics.mart_daily_revenue
    ORDER BY order_date DESC
""").df()
daily['order_date'] = pd.to_datetime(daily['order_date'])

this_week = daily[daily['order_date'] >= daily['order_date'].max() - timedelta(days=6)]
last_week = daily[
    (daily['order_date'] >= daily['order_date'].max() - timedelta(days=13)) &
    (daily['order_date'] <  daily['order_date'].max() - timedelta(days=6))
]

this_rev  = this_week['total_revenue'].sum()
last_rev  = last_week['total_revenue'].sum()
wow_pct   = ((this_rev - last_rev) / last_rev * 100) if last_rev > 0 else 0

this_orders = this_week['total_orders'].sum()
avg_order   = this_week['avg_order_value'].mean()

segments = conn.execute("""
    SELECT segment, COUNT(*) as customers,
           ROUND(AVG(total_revenue), 0) as avg_ltv
    FROM analytics.mart_customer_segments
    GROUP BY segment ORDER BY avg_ltv DESC
""").df()

top_category = conn.execute("""
    SELECT p.category,
           ROUND(SUM(o.quantity * o.unit_price), 0) AS revenue
    FROM analytics.stg_orders o
    JOIN analytics.stg_products p ON o.product_id = p.product_id
    WHERE o.is_completed = true
    GROUP BY p.category ORDER BY revenue DESC LIMIT 1
""").df()

high_risk = conn.execute("""
    SELECT COUNT(*) as cnt FROM analytics.mart_churn_predictions
    WHERE churn_risk = 'High'
""").fetchone()[0]

forecast_7 = conn.execute("""
    SELECT ROUND(SUM(predicted_revenue), 0) as total
    FROM analytics.mart_revenue_forecast
    WHERE record_type = 'forecast'
    LIMIT 7
""").fetchone()[0]

conn.close()

# ── Generate charts ───────────────────────────────────────────────────────────
chart_path = f'{REPORTS_DIR}/report_chart.png'
fig = plt.figure(figsize=(14, 10))
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

# Chart 1 — weekly revenue bar
ax1 = fig.add_subplot(gs[0, :])
week_data = daily.tail(14).sort_values('order_date')
bar_colors = ['#1D9E75' if i >= 7 else '#B5D4F4' for i in range(len(week_data))]
ax1.bar(week_data['order_date'].dt.strftime('%b %d'),
        week_data['total_revenue'], color=bar_colors)
ax1.set_title('Daily Revenue — Last 14 Days', fontweight='bold')
ax1.set_ylabel('Revenue (₹)')
ax1.tick_params(axis='x', rotation=45)
ax1.axvline(6.5, color='gray', linestyle='--', alpha=0.5)

# Chart 2 — segment pie
ax2 = fig.add_subplot(gs[1, 0])
seg_colors = ['#1D9E75', '#378ADD', '#EF9F27', '#E24B4A']
ax2.pie(segments['customers'], labels=segments['segment'],
        colors=seg_colors, autopct='%1.0f%%', startangle=90)
ax2.set_title('Customer Segments', fontweight='bold')

# Chart 3 — top products table
ax3 = fig.add_subplot(gs[1, 1])
ax3.axis('off')
table_data = [['Segment', 'Customers', 'Avg LTV']] + [
    [row['segment'], str(row['customers']), f"₹{int(row['avg_ltv']):,}"]
    for _, row in segments.iterrows()
]
tbl = ax3.table(cellText=table_data[1:], colLabels=table_data[0],
                loc='center', cellLoc='center')
tbl.auto_set_font_size(False)
tbl.set_fontsize(11)
tbl.scale(1.2, 1.8)
ax3.set_title('Segment LTV Summary', fontweight='bold', pad=20)

plt.savefig(chart_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Charts saved to {chart_path}")

# ── Build PDF ─────────────────────────────────────────────────────────────────
pdf_path = f'{REPORTS_DIR}/weekly_report.pdf'
doc      = SimpleDocTemplate(pdf_path, pagesize=A4,
                              leftMargin=2*cm, rightMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
styles   = getSampleStyleSheet()

title_style = ParagraphStyle('title',
    fontSize=22, fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1D9E75'),
    spaceAfter=6, alignment=TA_CENTER)
heading_style = ParagraphStyle('heading',
    fontSize=13, fontName='Helvetica-Bold',
    textColor=colors.HexColor('#2C2C2A'),
    spaceBefore=12, spaceAfter=4)
body_style = ParagraphStyle('body',
    fontSize=11, fontName='Helvetica',
    textColor=colors.HexColor('#444441'),
    leading=16, spaceAfter=6)
meta_style = ParagraphStyle('meta',
    fontSize=10, fontName='Helvetica',
    textColor=colors.HexColor('#888780'),
    alignment=TA_CENTER, spaceAfter=16)

direction = "up" if wow_pct >= 0 else "down"
sign      = "+" if wow_pct >= 0 else ""

story = [
    Paragraph("Weekly Revenue Intelligence Report", title_style),
    Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", meta_style),

    Paragraph("Executive Summary", heading_style),
    Paragraph(
        f"Revenue this week came in at <b>₹{this_rev:,.0f}</b>, "
        f"{direction} <b>{sign}{wow_pct:.1f}%</b> compared to last week's ₹{last_rev:,.0f}. "
        f"The business processed <b>{this_orders:,.0f} orders</b> with an average order "
        f"value of <b>₹{avg_order:,.0f}</b>.", body_style),

    Paragraph("Customer Health", heading_style),
    Paragraph(
        f"The top performing segment is <b>Champions</b> with "
        f"{int(segments[segments['segment']=='Champions']['customers'].values[0])} customers "
        f"and an average lifetime value of "
        f"₹{int(segments[segments['segment']=='Champions']['avg_ltv'].values[0]):,}. "
        f"There are currently <b>{high_risk} high-risk customers</b> flagged for churn — "
        f"these should be prioritised for a re-engagement campaign this week.", body_style),

    Paragraph("Top Category", heading_style),
    Paragraph(
        f"<b>{top_category['category'].values[0]}</b> remains the highest revenue "
        f"category at ₹{int(top_category['revenue'].values[0]):,} in total completed sales. "
        f"Consider increasing inventory and marketing spend here.", body_style),

    Paragraph("Revenue Outlook", heading_style),
    Paragraph(
        f"The forecasting model predicts <b>₹{int(forecast_7):,}</b> in revenue "
        f"over the next 7 days based on historical trends and seasonality patterns.", body_style),

    Spacer(1, 0.5*cm),
    Image(chart_path, width=16*cm, height=11*cm),
]

doc.build(story)
print(f"PDF saved to {pdf_path}")
