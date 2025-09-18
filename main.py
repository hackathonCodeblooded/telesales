import io

from boto3.dynamodb.conditions import Attr
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import boto3
import uuid
import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.sql import insert
from typing import Optional
from datetime import date
import diarization

import dynamoDb
from diarization import diarize_audio

# Create app instance
app = FastAPI()

# Allow specific origins
origins = [
  "https://local.edge.housing.com",  # your frontend
  # "http://localhost:3000",         # example if you also run locally
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,  # origins allowed
  allow_credentials=True,
  allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
  allow_headers=["*"],  # all headers
)

S3_BUCKET = "telesalesaudios"
AWS_REGION = 'us-east-1'
RDS_HOST = 'database-1.c0vcwyoyopo7.us-east-1.rds.amazonaws.com'
RDS_PORT = '3306'
DB_NAME = 'hackathon'
DB_USER = 'admin'
DB_PASSWORD = 'reahackathon'

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{DB_NAME}"

s3 = boto3.client("s3", region_name=AWS_REGION)

engine = create_engine(DATABASE_URL)
metadata = MetaData()

calls = Table(
  'calls', metadata,
  Column('id', Integer, primary_key=True),
  Column('agent_id', String(100)),
  Column('customer_phone_number', String(20)),
  Column('audio_s3_path', String(512)),
)


# Example DTO (request/response body)
class Item(BaseModel):
  id: int
  name: str
  price: float


# Root endpoint
@app.get("/")
def read_root():
  return {"message": "Hello, FastAPI!"}


# Path parameter
@app.get("/items/{item_id}")
def read_item(item_id: int):
  return {"item_id": item_id, "name": f"Item {item_id}"}


# # POST endpoint
# @app.post("/items")
# def create_item(item: Item):
#   return {"message": "Item created", "item": item}


@app.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    agent_id: int = Form(...),
    agent_name: str = Form("abcd"),
    customer_phone_number: str = Form(...)
):
  try:
    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ['.mp3', '.wav']:
      raise HTTPException(status_code=400,
                          detail="Invalid file type. Only .mp3 or .wav allowed.")

    print("File accepted:", original_filename)

    # Create unique filename to avoid overwriting in S3
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    audio_bytes = await file.read()
    # Upload to S3
    s3.upload_fileobj(
      io.BytesIO(audio_bytes),
      S3_BUCKET,
      unique_filename,
      ExtraArgs={"ContentType": file.content_type}
    )
    print("File uploaded to S3")

    # Create S3 URL
    s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
    print("S3 URL:", s3_url)
    
    if not agent_name:
        agent_name = f"Agent_{agent_id}"
        
    diarize_audio(audio_bytes, agent_id, customer_phone_number, s3_url, agent_name)
    return JSONResponse(
      content={"message": "File uploaded successfully", "s3_url": s3_url},
      status_code=200)

  except Exception as e:
    print("Error:", str(e))
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent-rating-data")
def get_agent_rating_data(
    agent_id: Optional[int] = Query(None, description="Agent ID"),
    customer_phone_number: Optional[str] = Query(None,
                                                 description="Customer phone number")
):
  # Validation: At least one parameter must be provided
  if not agent_id and not customer_phone_number:
    raise HTTPException(
      status_code=400,
      detail="At least one of agent_id or customer_phone_number must be provided"
    )

  # Mock response list (replace with DB/service logic)
  response = [
    {
      "instance_id": 1,
      "agent_id": agent_id if agent_id else "AGT001",
      "customer_phone_number": customer_phone_number if customer_phone_number else "1234567890",
      "overall_rating": 4.5,
      "status": "Active",
      "rating_parameter": [
        {"Sentiment": "good"}
      ]
    },
    {
      "instance_id": 2,
      "agent_id": "AGT002",
      "customer_phone_number": "9876543210",
      "overall_rating": 4.2,
      "status": "Inactive",
      "rating_parameter": [
        {"Sentiment": "average"}
      ]
    }
  ]
  return response


@app.get("/v2/agent-rating-data")
def get_agent_rating_dataV2(
    agent_id: Optional[int] = Query(None, description="Agent ID"),
    customer_phone_number: Optional[str] = Query(None,
                                                 description="Customer phone number")
):
  # Validation: At least one parameter must be provided
  if not agent_id and not customer_phone_number:
    raise HTTPException(
      status_code=400,
      detail="At least one of agent_id or customer_phone_number must be provided"
    )

  # Build query dynamically
  query = {}
  if agent_id:
    query["agent_id"] = agent_id
  if customer_phone_number:
    query["customer_phone_number"] = customer_phone_number

  filter_exp = (
    Attr("customer_phone_number").eq(str(customer_phone_number)) |
    Attr("agent_id").eq(agent_id)
  )

  # Fetch from Mongo
  results = dynamoDb.find_items(filter_exp)  # hide Mongo _id

  if not results:
    raise HTTPException(status_code=404, detail="No records found")

  response = []
  for idx, record in enumerate(results, start=1):
    response.append({
      "instance_id": idx,
      "agent_id": record.get("agent_id"),
      "customer_phone_number": record.get("customer_phone_number"),
      "overall_rating": record.get("agent_overall_rating", 0),
      "status": "Active" if record.get("converted", False) else "Inactive",
      "rating_parameter": [
        {"Customer Sentiment Score": record.get("customer_sentiment_score")},
        {"Conversation Quality Score": record.get(
          "conversation_quality_score")},
        {"Agent Tone Score": record.get("agent_tone_score")},
        {"Compliance Score": record.get("compliance_score")},
        {"Responsiveness Score": record.get("responsiveness_score")},
        {"Adaptability Score": record.get("adaptability_score")},
        {"Product Awareness Score": record.get("product_awareness_score")},
        {"Problem Resolution Score": record.get("problem_resolution_score")}
      ]
    })

  return response


@app.get("/agent-insights")
def get_agent_insights():
  response = {
    "agent_ratings": {
      "excellent": 45,
      "good": 78,
      "average": 23,
      "poor": 12
    },
    "performance_metrics": {
      "total_agents": 158,
      "top_performers": 45,
      "needs_improvement": 35,
      "new_agents": 18
    }
  }
  return response


@app.get("/overall-agents-metrics")
def get_overall_agents_metrics():
  response = {
    "overallMetrics": {
      "averageRating": 4.1,
      "totalAgents": 158,
      "totalRatings": 2847,
      "responseTime": "2.3 hours"
    },
    "topPerformers": [
      {"name": "Sarah Wilson", "rating": 4.9, "department": "Customer Support"},
      {"name": "David Chen", "rating": 4.8, "department": "Technical Support"},
      {"name": "Emily Davis", "rating": 4.7, "department": "Billing Support"}
    ],
    "departmentStats": [
      {"department": "Customer Support", "avgRating": 4.3, "agentCount": 65},
      {"department": "Technical Support", "avgRating": 4.0, "agentCount": 48},
      {"department": "Billing Support", "avgRating": 3.9, "agentCount": 45}
    ]
  }
  return response
  
  
@app.get("/get-all-data")
def get_all_data():
  return dynamoDb.fetch_all_items()
  
@app.get("/get-business-insights")
def get_business_insights(date_param: Optional[date] = Query(None, description="Filter by created_at date")):
  return diarization.get_business_insights(date_param)