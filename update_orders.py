#!/usr/bin/env python3
import json

# Read the orders file
with open('tools/data/orders.json', 'r') as f:
    data = json.load(f)

# Update all orders to use demo_user
for order in data['orders']:
    order['user_id'] = 'demo_user'
    order['email'] = 'demo_user@example.com'

# Write back
with open('tools/data/orders.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Updated {len(data['orders'])} orders to use demo_user")