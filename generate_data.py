import pandas as pd
import numpy as np
from faker import Faker
import json
import os
import random
from datetime import datetime, timedelta

fake = Faker('en_IN')
Faker.seed(42)
np.random.seed(42)
random.seed(42)

OUTPUT = 'data/raw'
os.makedirs(OUTPUT, exist_ok=True)

categories = {
    'Electronics': ['Wireless Earbuds', 'Phone Case', 'USB-C Hub', 'Portable Charger',
                    'Bluetooth Speaker', 'Laptop Stand', 'Webcam', 'Mechanical Keyboard'],
    'Apparel':     ['Cotton T-Shirt', 'Denim Jacket', 'Running Shorts', 'Hoodie',
                    'Polo Shirt', 'Formal Trousers', 'Sports Socks', 'Cap'],
    'Home':        ['Scented Candle', 'Cushion Cover', 'Wall Clock', 'Desk Organiser',
                    'Ceramic Mug', 'Bamboo Cutting Board', 'LED Fairy Lights', 'Photo Frame'],
    'Beauty':      ['Face Serum', 'Moisturiser', 'Lip Balm', 'Sunscreen SPF50',
                    'Hair Mask', 'Body Scrub', 'Eye Cream', 'Toner'],
    'Sports':      ['Yoga Mat', 'Resistance Bands', 'Water Bottle', 'Gym Gloves',
                    'Skipping Rope', 'Foam Roller', 'Protein Shaker', 'Ankle Support'],
}

products = []
product_id = 1
for category, items in categories.items():
    for name in items:
        cost  = round(random.uniform(200, 2000), 2)
        price = round(cost * random.uniform(1.4, 2.8), 2)
        products.append({
            'product_id':   f'P{product_id:03d}',
            'product_name': name,
            'category':     category,
            'cost_price':   cost,
            'list_price':   price,
        })
        product_id += 1

df_products = pd.DataFrame(products)
df_products.to_csv(f'{OUTPUT}/products.csv', index=False)
print(f'products.csv  — {len(df_products)} rows')

cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai',
          'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat']
channels = ['organic', 'paid_search', 'social_media', 'referral', 'email']

start_date = datetime(2022, 1, 1)
end_date   = datetime(2024, 6, 30)

customers = []
for i in range(1, 2001):
    signup = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    customers.append({
        'customer_id':         f'C{i:04d}',
        'name':                fake.name(),
        'email':               fake.email(),
        'city':                random.choice(cities),
        'signup_date':         signup.strftime('%Y-%m-%d'),
        'acquisition_channel': random.choices(channels, weights=[30,25,20,15,10])[0],
    })

df_customers = pd.DataFrame(customers)
df_customers.to_csv(f'{OUTPUT}/customers.csv', index=False)
print(f'customers.csv — {len(df_customers)} rows')

statuses = ['completed', 'completed', 'completed', 'returned', 'pending']
orders   = []

for i in range(1, 10001):
    customer   = random.choice(customers)
    signup_dt  = datetime.strptime(customer['signup_date'], '%Y-%m-%d')
    order_date = signup_dt + timedelta(days=random.randint(1, 730))
    if order_date > end_date:
        order_date = end_date
    product    = random.choice(products)
    quantity   = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 12, 8, 5])[0]
    unit_price = round(product['list_price'] * random.uniform(0.85, 1.0), 2)
    orders.append({
        'order_id':    f'O{i:05d}',
        'customer_id': customer['customer_id'],
        'product_id':  product['product_id'],
        'order_date':  order_date.strftime('%Y-%m-%d'),
        'quantity':    quantity,
        'unit_price':  unit_price,
        'status':      random.choice(statuses),
    })

df_orders = pd.DataFrame(orders)
df_orders.to_csv(f'{OUTPUT}/orders.csv', index=False)
print(f'orders.csv    — {len(df_orders)} rows')

event_types = ['page_view', 'page_view', 'page_view', 'add_to_cart', 'purchase']
events      = []

for i in range(1, 50001):
    customer   = random.choice(customers)
    product    = random.choice(products)
    signup_dt  = datetime.strptime(customer['signup_date'], '%Y-%m-%d')
    event_dt   = signup_dt + timedelta(
                     days=random.randint(0, 700),
                     hours=random.randint(0, 23),
                     minutes=random.randint(0, 59))
    if event_dt > end_date:
        event_dt = end_date
    events.append({
        'event_id':    f'E{i:06d}',
        'customer_id': customer['customer_id'],
        'product_id':  product['product_id'],
        'event_type':  random.choices(event_types)[0],
        'event_time':  event_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'page':        f"/product/{product['product_id']}",
        'session_id':  f'S{random.randint(1,15000):05d}',
    })

with open(f'{OUTPUT}/events.jsonl', 'w') as f:
    for e in events:
        f.write(json.dumps(e) + '\n')

print(f'events.jsonl  — {len(events)} rows')
print('\nAll data generated successfully.')
