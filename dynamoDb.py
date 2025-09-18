import json
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import re

from TranscriptionDto import TranscriptDTO

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
        
def safe_json_loads(raw_str: str):
    # 1. Remove Markdown code fences like ```json ... ```
    raw_str = re.sub(r"^```json", "", raw_str.strip())
    raw_str = re.sub(r"^```", "", raw_str.strip())
    raw_str = re.sub(r"```$", "", raw_str.strip())
    
    # 2. Strip again just in case
    raw_str = raw_str.strip()

    try:
        return json.loads(raw_str)
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        return {}


def map_analysis_to_dto(
    transcript: str,
    agent_id: int,
    customer_phone_number: str,
    audio_s3_path: str,
    agent_name: str,
    call_duration: float,
    analysis_json: str
) -> TranscriptDTO:
  """
  Maps the JSON response from Gemini into a TranscriptDTO object.
  """
  cleaned_json = safe_json_loads(analysis_json)  
  try:
    analysis_data = cleaned_json
  except json.JSONDecodeError:
    analysis_data = {}
    
  print("json analysis: ", cleaned_json) 
  print("json data:", analysis_data)

  # Convert all float values to Decimal if using DynamoDB

  dto = TranscriptDTO(
    transcript=transcript,
    agent_id=agent_id,
    agent_name=agent_name,
    customer_phone_number=customer_phone_number,
    audio_s3_path=audio_s3_path,
    call_duration=call_duration,
    # Map analysis fields
    agent_overall_rating=(analysis_data.get("agent_overall_rating")),
    customer_sentiment_score=(
      analysis_data.get("customer_sentiment_score")),
    conversation_quality_score=(
      analysis_data.get("conversation_quality_score")),
    agent_tone_score=(analysis_data.get("agent_tone_score")),
    compliance_score=(analysis_data.get("compliance_score")),
    responsiveness_score=(analysis_data.get("responsiveness_score")),
    adaptability_score=(analysis_data.get("adaptability_score")),
    product_awareness_score=(
      analysis_data.get("product_awareness_score")),
    problem_resolution_score=(
      analysis_data.get("problem_resolution_score")),
    call_summarization=analysis_data.get("call_summarization"),
    actionable_insights=analysis_data.get("actionable_insights")
  )
  
  print(dto)

  return dto


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
