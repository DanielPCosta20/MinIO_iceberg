"""
Cleanup script for Iceberg catalog resources.

This script allows you to drop namespaces and delete warehouses.
Configure the resources to clean up by modifying the lists at the top of the script.
"""

import json
import os
import sys

import requests
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.exceptions import (
    NoSuchNamespaceError,
    NoSuchTableError,
    NamespaceNotEmptyError,
)

# Add sigv4 to path for warehouse operations
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from sigv4 import sign

# Configuration
ENDPOINT = "http://localhost:9000"
CATALOG_URL = f"{ENDPOINT}/_iceberg"
# Note: CATALOG_NAME is just a client-side identifier for the PyIceberg connection.
# It's not stored on the server - only warehouses and namespaces exist server-side.
CATALOG_NAME = "cleanup"

access_key = "minioadmin"
secret_key = "minioadmin"

# Set AWS environment variables for SigV4 authentication
os.environ["AWS_ACCESS_KEY_ID"] = str(access_key)
os.environ["AWS_SECRET_ACCESS_KEY"] = str(secret_key)
os.environ["AWS_REGION"] = "local"

# ============================================================================
# CONFIGURATION: Specify what to clean up
# ============================================================================

# Warehouses to delete (as strings)
# Namespaces within each warehouse will be discovered and deleted automatically
WAREHOUSES_TO_DELETE = [
    "lab",
]

# ============================================================================


def delete_warehouse(warehouse_name: str) -> bool:
    """Delete a warehouse. Returns True if deleted, False otherwise."""
    print(f"Deleting warehouse '{warehouse_name}'...")

    warehouse_url = f"{CATALOG_URL}/v1/warehouses/{warehouse_name}"
    headers_to_sign = {
        "content-type": "application/json",
    }

    aws_sign = sign(
        "DELETE",
        url=warehouse_url,
        body="",
        host=ENDPOINT,
        access_key=access_key,
        secret_key=secret_key,
        headers=headers_to_sign
    )

    response = requests.delete(
        warehouse_url,
        headers=dict(aws_sign.headers)
    )

    if response.status_code == 204:
        print(f"✓ Deleted warehouse '{warehouse_name}'")
        return True
    elif response.status_code == 404:
        print(f"⚠ Warehouse '{warehouse_name}' does not exist")
        return False
    else:
        print(f"⚠ Warning: Unexpected response when deleting warehouse: {response.status_code}")
        print(f"  Response: {response.content.decode()}")
        return False


def drop_namespace(catalog: RestCatalog, namespace: tuple) -> bool:
    """Drop a namespace. Returns True if dropped, False otherwise."""
    namespace_str = ".".join(namespace)
    print(f"Dropping namespace '{namespace_str}'...")

    try:
        # Check if namespace exists
        try:
            # Try to list tables - this will fail if namespace doesn't exist
            tables = list(catalog.list_tables(namespace))

            # Check if namespace is empty
            if tables:
                print(f"✗ Cannot drop namespace '{namespace_str}': it contains {len(tables)} table(s)")
                print(f"  Tables: {[str(t) for t in tables]}")
                print(f"  Please drop all tables first or use a different cleanup method")
                return False
        except NoSuchNamespaceError:
            print(f"⚠ Namespace '{namespace_str}' does not exist")
            return False

        # Namespace exists and is empty, proceed with drop
        catalog.drop_namespace(namespace)
        print(f"✓ Dropped namespace '{namespace_str}'")
        return True

    except NoSuchNamespaceError:
        print(f"⚠ Namespace '{namespace_str}' does not exist")
        return False
    except NamespaceNotEmptyError:
        print(f"✗ Cannot drop namespace '{namespace_str}': it is not empty")
        return False
    except Exception as e:
        print(f"✗ Error dropping namespace '{namespace_str}': {e}")
        return False


def list_warehouses() -> list:
    """List all warehouses. Returns a list of warehouse names."""
    warehouse_url = f"{CATALOG_URL}/v1/warehouses"
    headers_to_sign = {
        "content-type": "application/json",
    }

    aws_sign = sign(
        "GET",
        url=warehouse_url,
        body="",
        host=ENDPOINT,
        access_key=access_key,
        secret_key=secret_key,
        headers=headers_to_sign
    )

    response = requests.get(
        warehouse_url,
        headers=dict(aws_sign.headers)
    )

    if response.status_code == 200:
        data = response.json()
        # API returns warehouses as a simple list of strings
        return data.get("warehouses", [])
    return []


def create_catalog_for_warehouse(warehouse_name: str) -> RestCatalog:
    """Create a catalog connection for a specific warehouse."""
    return RestCatalog(
        name=CATALOG_NAME,
        warehouse=warehouse_name,
        uri=CATALOG_URL,
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


def cleanup_warehouse(warehouse_name: str) -> bool:
    """Clean up all namespaces in a warehouse and delete it. Returns True if successful."""
    print(f"Cleaning up warehouse '{warehouse_name}'...")

    # Create catalog connection for this warehouse
    try:
        catalog = create_catalog_for_warehouse(warehouse_name)
    except Exception as e:
        print(f"✗ Could not connect to warehouse '{warehouse_name}': {e}")
        return False

    # List all namespaces in this warehouse
    try:
        namespaces = list(catalog.list_namespaces())
        print(f"  Found {len(namespaces)} namespace(s) in warehouse '{warehouse_name}'")
    except Exception as e:
        print(f"✗ Could not list namespaces in warehouse '{warehouse_name}': {e}")
        return False

    # Drop all namespaces
    if namespaces:
        print()
        dropped_count = 0
        for namespace in namespaces:
            if drop_namespace(catalog, namespace):
                dropped_count += 1
        print(f"  Dropped {dropped_count} of {len(namespaces)} namespace(s)")
        print()

    # Now delete the warehouse
    return delete_warehouse(warehouse_name)


def main():
    """Main cleanup function."""
    print("=" * 60)
    print("Iceberg Catalog Cleanup Script")
    print("=" * 60)
    print(f"Catalog URL: {CATALOG_URL}")
    print(f"Warehouses to delete: {WAREHOUSES_TO_DELETE}")
    print()

    # Delete warehouses (with automatic namespace cleanup)
    if WAREHOUSES_TO_DELETE:
        print("=" * 60)
        print("Cleaning Up Warehouses")
        print("=" * 60)
        deleted_count = 0
        for warehouse in WAREHOUSES_TO_DELETE:
            print()
            if cleanup_warehouse(warehouse):
                deleted_count += 1
            print()
        print(f"Summary: Deleted {deleted_count} of {len(WAREHOUSES_TO_DELETE)} warehouse(s)")
    else:
        print("No warehouses specified for deletion.")

    # Verify cleanup
    print()
    print("=" * 60)
    print("Verification")
    print("=" * 60)
    remaining_warehouses = list_warehouses()
    deleted_warehouses = [w for w in WAREHOUSES_TO_DELETE if w not in remaining_warehouses]
    failed_warehouses = [w for w in WAREHOUSES_TO_DELETE if w in remaining_warehouses]

    if failed_warehouses:
        print(f"⚠ Warning: {len(failed_warehouses)} warehouse(s) could not be deleted:")
        for w in failed_warehouses:
            print(f"    - {w}")
        print()
        print("=" * 60)
        print("Cleanup completed with warnings")
        print("=" * 60)
    else:
        print(f"✓ All {len(deleted_warehouses)} specified warehouse(s) have been deleted")
        print()
        print("=" * 60)
        print("Cleanup completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    main()

