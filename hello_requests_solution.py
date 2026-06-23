import json
import os
import sys

import requests

# Add sigv4 to path
sys.path.append(os.path.abspath(os.curdir))
print(sys.path)

from sigv4 import sign

# Configuration
CATALOG_URL = "http://localhost:9000/_iceberg"
WAREHOUSE = "lab"
HOST = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

create_payload = {"name": WAREHOUSE}
warehouse_url = f"{CATALOG_URL}/v1/warehouses"
payload = json.dumps(create_payload)
headers_to_sign = {
    "content-type": "application/json",
    "content-length": str(len(payload))
}

aws_sign = sign(
    "POST",
    url=warehouse_url,
    body=payload,
    host=HOST,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    headers=headers_to_sign
)

response = requests.post(
    warehouse_url,
    data=payload,
    headers=dict(aws_sign.headers)
)

print(f"Status: {response.status_code}")
print(f"Response: {response.content}")
