#!/usr/bin/env python3
"""
Clean all items from DynamoDB socratic_core table.
Uses batch operations for efficiency.
"""

import boto3
import sys
from botocore.exceptions import ClientError

PROFILE = "mvp"
REGION = "us-east-1"
TABLE_NAME = "socratic_core"

def main():
    # Initialize DynamoDB client
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)

    print(f"🗑️  Deleting all items from table: {TABLE_NAME}")
    print(f"   Profile: {PROFILE}")
    print(f"   Region: {REGION}")
    print()

    # Scan table to get all items
    print("📋 Scanning table for items...")
    items = []
    scan_kwargs = {}

    try:
        while True:
            response = table.scan(**scan_kwargs)
            items.extend(response.get("Items", []))

            # Check if there are more items to scan
            if "LastEvaluatedKey" not in response:
                break
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            print(f"   Scanned {len(items)} items so far...")

    except ClientError as e:
        print(f"❌ Error scanning table: {e}")
        sys.exit(1)

    print(f"✓ Found {len(items)} items to delete")
    print()

    if len(items) == 0:
        print("✅ Table is already empty")
        return

    # Delete items in batches of 25 (DynamoDB limit)
    print("🗑️  Deleting items...")
    deleted_count = 0
    batch_size = 25

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        with table.batch_writer() as writer:
            for item in batch:
                try:
                    writer.delete_item(
                        Key={
                            "PK": item["PK"],
                            "SK": item["SK"]
                        }
                    )
                    deleted_count += 1

                    if deleted_count % 50 == 0:
                        print(f"   Deleted {deleted_count}/{len(items)} items...")

                except ClientError as e:
                    print(f"   ⚠️  Failed to delete PK={item['PK']}, SK={item['SK']}: {e}")

    print(f"\n✅ Successfully deleted {deleted_count} items")
    print()


if __name__ == "__main__":
    main()
