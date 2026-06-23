"""
Hello World: Create a warehouse using the REST API.

This script demonstrates:
- Using the requests library to call AIStor Tables REST API
- AWS SigV4 authentication for API calls
- Creating a warehouse (the first step in using AIStor Tables)

EXERCISES IN THIS SCRIPT:
- Exercise 1: Configure your warehouse name
"""

import json
import os
import sys

import requests

# Add sigv4 to path
sys.path.append(os.path.abspath(os.curdir))

from sigv4 import sign

# Configuration
CATALOG_URL = "http://localhost:9000/_iceberg"
HOST = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

# ============================================================
# EXERCISE 1: Configure your warehouse name
# ============================================================
# TODO: Replace REPLACE_ME with your warehouse name
# HINT: Use a simple name like "lab" or "my-warehouse"
# HINT: Warehouse names should be lowercase with hyphens
# TODO: Don't forget to update the cleanup.py script with the same value

WAREHOUSE = "REPLACE_ME"

# ============================================================
# Validation: Ensure Exercise 1 is completed
# ============================================================
if WAREHOUSE == "REPLACE_ME":
    print("=" * 60)
    print("ERROR: Please complete Exercise 1 first!")
    print("=" * 60)
    print("\nEdit this file and replace REPLACE_ME with your warehouse name.")
    print("\nExample:")
    print('  WAREHOUSE = "lab"')
    print("\nThen run this script again.")
    sys.exit(1)

# Build the request
create_payload = {"name": WAREHOUSE}
warehouse_url = f"{CATALOG_URL}/v1/warehouses"
payload = json.dumps(create_payload)
headers_to_sign = {
    "content-type": "application/json",
    "content-length": str(len(payload))
}

# Sign the request with AWS SigV4
aws_sign = sign(
    "POST",
    url=warehouse_url,
    body=payload,
    host=HOST,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    headers=headers_to_sign
)

# Send the request
print("=" * 60)
print("Creating Warehouse with REST API")
print("=" * 60)
print(f"Warehouse name: {WAREHOUSE}")
print(f"API endpoint: {warehouse_url}")
print()

response = requests.post(
    warehouse_url,
    data=payload,
    headers=dict(aws_sign.headers)
)

# Display the result
print(f"Status: {response.status_code}")

if response.status_code == 201 or response.status_code == 200:
    print(f"Response: {response.content.decode()}")
    print()
    print("=" * 60)
    print(f"Success! Warehouse '{WAREHOUSE}' created.")
    print("=" * 60)
    print("\nYou can verify with: mc ls aistor")
    print(f"You should see a bucket named '{WAREHOUSE}'")
elif response.status_code == 409:
    print(f"Warehouse '{WAREHOUSE}' already exists (this is OK)")
else:
    print(f"Response: {response.content.decode()}")
    print("\nUnexpected response. Please check your configuration.")

print()
print("-" * 60)
print("Exercise Status:")
print("-" * 60)
print(f"  Exercise 1: Warehouse name configured as '{WAREHOUSE}'")
print("\nNext: Run hello_pyiceberg.py to work with the catalog")
