# E-commerce Revenue Intelligence Platform

A full end-to-end data engineering and analytics project built to demonstrate production-grade skills across ingestion, transformation, modelling, and visualisation.

## Live Demo
> Streamlit dashboard — deploy instructions below

## What this project does
- Ingests raw e-commerce data (orders, customers, products, clickstream events) into a DuckDB warehouse
- Transforms raw data through a layered dbt architecture (staging → intermediate → marts)
- Validates data quality across 14 automated checks
- Segments customers using RFM scoring and KMeans clustering
- Predicts churn risk using logistic regression (AUC-ROC > 0.75)
- Forecasts 30-day revenue using Facebook Prophet
- Serves insights through an interactive 4-page Streamlit dashboard
- Generates automated weekly PDF reports with narrative insights

## Tech Stack
| Layer | Tools |
|---|---|
| Data generation | Python, Faker |
| Warehouse | DuckDB |
| Transformation | dbt-duckdb |
| Data quality | Custom expectation suite |
| Modelling | scikit-learn, Prophet |
| Visualisation | Streamlit, Plotly |
| Reporting | ReportLab, Matplotlib |

## Project Structure
```
ecommerce-intelligence/
├── data/raw/              # Source CSVs and JSONL
├── generate_data.py       # Fake data generator
├── ingestion/
│   ├── pipeline.py        # DuckDB ingestion pipeline
│   └── data_quality.py    # 14 automated quality checks
├── dbt_project/
│   └── ecommerce_dbt/     # Staging, intermediate, mart models
├── models/
│   ├── 01_ltv_rfm.ipynb   # RFM segmentation
│   ├── 02_churn_model.ipynb
│   └── 03_revenue_forecast.ipynb
├── dashboard/app.py       # Streamlit dashboard
└── reports/weekly_report.py
```

## How to run locally
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-intelligence
cd ecommerce-intelligence
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 generate_data.py
python3 ingestion/pipeline.py
cd dbt_project/ecommerce_dbt && dbt run && cd ../..
streamlit run dashboard/app.py
```

## Key findings
- **Champions segment** (31% of customers) drives the majority of revenue with avg LTV 3x higher than At Risk customers
- **421 high-risk churn customers** identified — targeted re-engagement could recover significant revenue
- **Apparel and Beauty** are the highest margin categories
- **30-day revenue forecast** generated with confidence intervals using Prophet seasonality model
