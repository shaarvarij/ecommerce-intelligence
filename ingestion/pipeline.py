import pandas as pd
import duckdb
import json
import os
from datetime import datetime

DB_PATH   = 'ecommerce.db'
RAW_PATH  = 'data/raw'

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_conn():
    return duckdb.connect(DB_PATH)

def create_raw_schema(conn):
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
    log("Schema 'raw' ready")

def load_products(conn):
    df = pd.read_csv(f'{RAW_PATH}/products.csv')
    conn.execute("DROP TABLE IF EXISTS raw.products")
    conn.execute("""
        CREATE TABLE raw.products (
            product_id   VARCHAR,
            product_name VARCHAR,
            category     VARCHAR,
            cost_price   DOUBLE,
            list_price   DOUBLE
        )
    """)
    conn.execute("INSERT INTO raw.products SELECT * FROM df")
    log(f"raw.products loaded — {len(df)} rows")

def load_customers(conn):
    df = pd.read_csv(f'{RAW_PATH}/customers.csv')
    conn.execute("DROP TABLE IF EXISTS raw.customers")
    conn.execute("""
        CREATE TABLE raw.customers (
            customer_id         VARCHAR,
            name                VARCHAR,
            email               VARCHAR,
            city                VARCHAR,
            signup_date         VARCHAR,
            acquisition_channel VARCHAR
        )
    """)
    conn.execute("INSERT INTO raw.customers SELECT * FROM df")
    log(f"raw.customers loaded — {len(df)} rows")

def load_orders(conn):
    df = pd.read_csv(f'{RAW_PATH}/orders.csv')
    conn.execute("DROP TABLE IF EXISTS raw.orders")
    conn.execute("""
        CREATE TABLE raw.orders (
            order_id    VARCHAR,
            customer_id VARCHAR,
            product_id  VARCHAR,
            order_date  VARCHAR,
            quantity    INTEGER,
            unit_price  DOUBLE,
            status      VARCHAR
        )
    """)
    conn.execute("INSERT INTO raw.orders SELECT * FROM df")
    log(f"raw.orders loaded — {len(df)} rows")

def load_events(conn):
    records = []
    with open(f'{RAW_PATH}/events.jsonl', 'r') as f:
        for line in f:
            records.append(json.loads(line.strip()))
    df = pd.DataFrame(records)
    conn.execute("DROP TABLE IF EXISTS raw.events")
    conn.execute("""
        CREATE TABLE raw.events (
            event_id    VARCHAR,
            customer_id VARCHAR,
            product_id  VARCHAR,
            event_type  VARCHAR,
            event_time  VARCHAR,
            page        VARCHAR,
            session_id  VARCHAR
        )
    """)
    conn.execute("INSERT INTO raw.events SELECT * FROM df")
    log(f"raw.events loaded — {len(df)} rows")

def log_run(conn, status):
    conn.execute("CREATE TABLE IF NOT EXISTS raw.pipeline_runs (run_time VARCHAR, status VARCHAR)")
    conn.execute(f"INSERT INTO raw.pipeline_runs VALUES ('{datetime.now()}', '{status}')")

def verify(conn):
    print()
    print("── Verification ──────────────────────────────")
    tables = ['raw.products', 'raw.customers', 'raw.orders', 'raw.events']
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<25} {count:>6} rows")
    print("──────────────────────────────────────────────")

def run_all():
    log("Pipeline starting...")
    conn = get_conn()
    try:
        create_raw_schema(conn)
        load_products(conn)
        load_customers(conn)
        load_orders(conn)
        load_events(conn)
        log_run(conn, 'success')
        verify(conn)
        log("Pipeline complete.")
    except Exception as e:
        log(f"Pipeline FAILED: {e}")
        log_run(conn, f'failed: {e}')
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run_all()
