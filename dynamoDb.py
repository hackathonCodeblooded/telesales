import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB Setup ---
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")  # change region if needed

# Table reference (make sure you create the table first in DynamoDB console)
# Primary key should be something like `id` (string)
table = dynamodb.Table("calls")


def insert_one(document: dict):
    """Insert one document into DynamoDB"""
    # Add unique ID if not already present
    if "id" not in document:
        document["id"] = str(uuid.uuid4())

    document["created_at"] = datetime.utcnow().isoformat()
    document["updated_at"] = datetime.utcnow().isoformat()

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
