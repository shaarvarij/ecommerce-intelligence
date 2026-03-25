import duckdb
import json
from datetime import datetime

DB_PATH = 'ecommerce.db'

results = []
passed  = 0
failed  = 0

def check(name, query, expectation):
    global passed, failed
    conn   = duckdb.connect(DB_PATH)
    result = conn.execute(query).fetchone()[0]
    conn.close()
    ok     = expectation(result)
    status = 'PASS' if ok else 'FAIL'
    if ok:
        passed += 1
    else:
        failed += 1
    results.append({
        'check':       name,
        'result':      str(result),
        'status':      status,
        'checked_at':  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    icon = 'v' if ok else 'X'
    print(f"  [{icon}] {name:<55} result={result}")

print()
print("Running data quality checks...")
print("─" * 70)

print()
print("[ raw layer ]")
check(
    "raw.orders row count > 9000",
    "SELECT COUNT(*) FROM raw.orders",
    lambda x: x > 9000
)
check(
    "raw.customers row count > 1900",
    "SELECT COUNT(*) FROM raw.customers",
    lambda x: x > 1900
)
check(
    "raw.orders has no null order_ids",
    "SELECT COUNT(*) FROM raw.orders WHERE order_id IS NULL",
    lambda x: x == 0
)
check(
    "raw.orders unit_price always positive",
    "SELECT COUNT(*) FROM raw.orders WHERE unit_price <= 0",
    lambda x: x == 0
)
check(
    "raw.orders quantity always positive",
    "SELECT COUNT(*) FROM raw.orders WHERE quantity <= 0",
    lambda x: x == 0
)
check(
    "raw.orders status values are valid",
    "SELECT COUNT(*) FROM raw.orders WHERE status NOT IN ('completed','returned','pending')",
    lambda x: x == 0
)

print()
print("[ staging layer ]")
check(
    "stg_orders line_revenue always positive",
    "SELECT COUNT(*) FROM analytics.stg_orders WHERE line_revenue <= 0",
    lambda x: x == 0
)
check(
    "stg_customers emails are lowercase",
    "SELECT COUNT(*) FROM analytics.stg_customers WHERE email != lower(email)",
    lambda x: x == 0
)
check(
    "stg_products margin_pct between 0 and 100",
    "SELECT COUNT(*) FROM analytics.stg_products WHERE margin_pct < 0 OR margin_pct > 100",
    lambda x: x == 0
)

print()
print("[ mart layer ]")
check(
    "mart_daily_revenue has no negative revenue days",
    "SELECT COUNT(*) FROM analytics.mart_daily_revenue WHERE total_revenue < 0",
    lambda x: x == 0
)
check(
    "mart_daily_revenue covers > 400 days",
    "SELECT COUNT(DISTINCT order_date) FROM analytics.mart_daily_revenue",
    lambda x: x > 400
)
check(
    "mart_customer_lifetime total_revenue always positive",
    "SELECT COUNT(*) FROM analytics.mart_customer_lifetime WHERE total_revenue < 0",
    lambda x: x == 0
)
check(
    "mart_customer_lifetime no customer has 0 orders",
    "SELECT COUNT(*) FROM analytics.mart_customer_lifetime WHERE total_orders = 0",
    lambda x: x == 0
)
check(
    "mart_product_performance covers all 5 categories",
    "SELECT COUNT(DISTINCT category) FROM analytics.mart_product_performance",
    lambda x: x == 5
)

print()
print("─" * 70)
total = passed + failed
print(f"  Results: {passed}/{total} checks passed", end="")
if failed == 0:
    print("  — All good!")
else:
    print(f"  — {failed} check(s) need attention")
print()

with open('reports/data_quality_report.json', 'w') as f:
    json.dump({
        'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'passed':   passed,
        'failed':   failed,
        'total':    total,
        'checks':   results
    }, f, indent=2)

print(f"  Report saved to reports/data_quality_report.json")
print()
