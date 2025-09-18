import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# --- DynamoDB Setup ---
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")  # change region if needed

# Table reference (make sure you create the table first in DynamoDB console)
# Primary key should be something like `id` (string)
table = dynamodb.Table("calls")

def convert_floats_to_decimal(obj):
    """Recursively convert float values in dict/list to Decimal"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def insert_one(document: dict):
    """Insert one document into DynamoDB"""
    # Add unique ID if not already present
    if "id" not in document:
        document["id"] = str(uuid.uuid4())


    document["created_at"] = datetime.utcnow().isoformat()
    document["updated_at"] = datetime.utcnow().isoformat()
    document["call_id"] = int(uuid.uuid4().int >> 64)
    document = convert_floats_to_decimal(document)

    try:
        table.put_item(Item=document)
        print(f"Inserted into DynamoDB: {document['id']}")
    except ClientError as e:
        print("DynamoDB insert_one error:", e)
        raise e

def insert_many(documents: list):
    """Batch insert multiple documents"""
    with table.batch_writer() as batch:
        for doc in documents:
            doc["created_at"] = datetime.utcnow().isoformat()
            doc["updated_at"] = datetime.utcnow().isoformat()
            batch.put_item(Item=doc)


def get_by_id(call_id: str):
  response = table.get_item(Key={"call_id": call_id})
  return response.get("Item")


def find_items(filter_expression):
  response = table.scan(
    FilterExpression=filter_expression
  )
  return response["Items"]

def fetch_all_items():
    items = []
    response = table.scan()  # fetch all fields
    items.extend(response.get("Items", []))

    # Handle pagination if table has more than 1 MB of data
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get("Items", []))

    return items
