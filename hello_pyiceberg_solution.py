import json
import os
import sys

import requests
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.exceptions import (
    NamespaceAlreadyExistsError,
    NoSuchNamespaceError,
    NoSuchTableError,
)

# Add sigv4 to path for warehouse creation
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from sigv4 import sign

ENDPOINT = "http://localhost:9000"
CATALOG_URL = f"{ENDPOINT}/_iceberg"
WAREHOUSE = "lab"
CATALOG_NAME = "first_catalog"

access_key = "minioadmin"
secret_key = "minioadmin"

# Set AWS environment variables for SigV4 authentication
os.environ["AWS_ACCESS_KEY_ID"] = str(access_key)
os.environ["AWS_SECRET_ACCESS_KEY"] = str(secret_key)
os.environ["AWS_REGION"] = "local"

def create_warehouse_if_needed(warehouse_name: str) -> bool:
    """Create a warehouse if it doesn't exist. Returns True if created, False if already exists."""
    print(f"Checking if warehouse '{warehouse_name}' exists...")

    create_payload = {"name": warehouse_name}
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
        host=ENDPOINT,
        access_key=access_key,
        secret_key=secret_key,
        headers=headers_to_sign
    )

    response = requests.post(
        warehouse_url,
        data=payload,
        headers=dict(aws_sign.headers)
    )

    if response.status_code == 201:
        print(f"✓ Created warehouse '{warehouse_name}'")
        return True
    elif response.status_code == 409:
        print(f"✓ Warehouse '{warehouse_name}' already exists")
        return False
    else:
        print(f"⚠ Warning: Unexpected response when creating warehouse: {response.status_code}")
        print(f"  Response: {response.content.decode()}")
        return False


# Create the catalog connection
print("=" * 60)
print("Iceberg Catalog Hello World")
print("=" * 60)
print(f"Connecting to catalog at: {CATALOG_URL}")
print(f"Warehouse: {WAREHOUSE}")
print()

# Create warehouse first before connecting to catalog
print("Ensuring warehouse exists...")
create_warehouse_if_needed(WAREHOUSE)
print()

catalog = RestCatalog(
    name=CATALOG_NAME,
    warehouse=WAREHOUSE,
    uri=CATALOG_URL,
    token="local",
    type="rest",
    **{
        "s3.access-key-id": access_key,
        "s3.secret-access-key": secret_key,
        "s3.endpoint": ENDPOINT,
        "s3.path-style-access": "true",
        "rest.sigv4-enabled": "true",
        "rest.signing-name": "s3tables",
        "rest.signing-region": "local",
    },
)

# Try to connect to catalog
print("Attempting to connect to catalog...")
try:
    namespaces = list(catalog.list_namespaces())
    print(f"✓ Successfully connected to Iceberg catalog!")
    print(f"✓ Found {len(namespaces)} namespace(s):")
    for namespace in namespaces:
        print(f"  - {namespace}")
except Exception as e:
    print(f"✗ Error connecting to catalog: {e}")
    print("\nPlease check:")
    print("  1. Is the AIStor service running? (docker-compose up)")
    print("  2. Is the catalog URL correct?")
    print("  3. Are the credentials correct?")
    raise

print()

# Demonstrate namespace creation
NAMESPACE = ("default",)  # Namespace as a tuple
print(f"Creating namespace '{NAMESPACE[0]}'...")
try:
    catalog.create_namespace(NAMESPACE)
    print(f"✓ Created namespace '{NAMESPACE[0]}'")
except NamespaceAlreadyExistsError:
    print(f"✓ Namespace '{NAMESPACE[0]}' already exists")
except Exception as e:
    print(f"⚠ Could not create namespace: {e}")

print()

# Create a second namespace to demonstrate multiple namespaces
NAMESPACE_2 = ("test",)
print(f"Creating second namespace '{NAMESPACE_2[0]}'...")
try:
    catalog.create_namespace(NAMESPACE_2)
    print(f"✓ Created namespace '{NAMESPACE_2[0]}'")
except NamespaceAlreadyExistsError:
    print(f"✓ Namespace '{NAMESPACE_2[0]}' already exists")
except Exception as e:
    print(f"⚠ Could not create namespace: {e}")

print()

# List namespaces to show what we have
print("Listing all namespaces...")
namespaces = list(catalog.list_namespaces())
print(f"✓ Found {len(namespaces)} namespace(s):")
for namespace in namespaces:
    print(f"  - {namespace}")

# List tables in namespaces
if namespaces:
    print()
    for namespace in namespaces:
        print(f"Listing tables in namespace {namespace}...")
        try:
            tables = list(catalog.list_tables(namespace))
            if tables:
                print(f"✓ Found {len(tables)} table(s):")
                for table in tables:
                    print(f"  - {table}")
            else:
                print(f"  (No tables found)")
        except Exception as e:
            print(f"  (Could not list tables: {e})")

print()

# Demonstrate checking if table exists (without exceptions)
TEST_TABLE_NAME = "non_existent_table"
TEST_NAMESPACE = ("default",)
print(f"Checking if table '{TEST_TABLE_NAME}' exists in namespace '{TEST_NAMESPACE[0]}'...")
try:
    # List all tables in the namespace and check if our table is in the list
    tables = list(catalog.list_tables(TEST_NAMESPACE))
    table_identifier = TEST_NAMESPACE + (TEST_TABLE_NAME,)

    if table_identifier in tables:
        print(f"✓ Table '{TEST_TABLE_NAME}' exists")
    else:
        print(f"✓ Table '{TEST_TABLE_NAME}' does not exist")
except NoSuchNamespaceError:
    print(f"✗ Namespace '{TEST_NAMESPACE[0]}' does not exist")
except Exception as e:
    print(f"⚠ Error checking table: {e}")

print()

# Demonstrate exception handling patterns
print("Demonstrating exception handling patterns...")
print("  Common PyIceberg exceptions:")
print("    • NamespaceAlreadyExistsError - when creating existing namespace")
print("    • NoSuchNamespaceError - when accessing non-existent namespace")
print("    • NoSuchTableError - when accessing non-existent table")
print("  Always wrap catalog operations in try/except blocks!")

print()
print("=" * 60)
print("✓ Hello World completed successfully!")
print("=" * 60)
print("\nYou've successfully:")
print("  • Connected to the Iceberg catalog")
print("  • Created/verified the warehouse")
print("  • Created/verified namespaces")
print("  • Listed namespaces and tables")
print("  • Checked table existence")
print("  • Learned exception handling patterns")