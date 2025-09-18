from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import boto3
import uuid
import os
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.sql import insert

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


# POST endpoint
@app.post("/items")
def create_item(item: Item):
  return {"message": "Item created", "item": item}


@app.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    agent_id: str = Form(...),
    customer_phone_number: str = Form(...)
):
  try:
    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ['.mp3', '.mp4']:
      raise HTTPException(status_code=400,
                          detail="Invalid file type. Only .mp3 or .mp4 allowed.")

    print("File accepted:", original_filename)

    # Create unique filename to avoid overwriting in S3
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"

    # Upload to S3
    s3.upload_fileobj(
      file.file,
      S3_BUCKET,
      unique_filename,
      ExtraArgs={"ContentType": file.content_type}
    )
    print("File uploaded to S3")

    # Create S3 URL
    s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
    print("S3 URL:", s3_url)

    # Insert data into DB
    with engine.connect() as conn:
      stmt = insert(calls).values(
        agent_id=agent_id,
        customer_phone_number=customer_phone_number,
        audio_s3_path=s3_url
      )
      conn.execute(stmt)
      conn.commit()
      print("Inserted metadata into DB")

    return JSONResponse(
      content={"message": "File uploaded successfully", "s3_url": s3_url},
      status_code=200)

  except Exception as e:
    print("Error:", str(e))
    raise HTTPException(status_code=500, detail=str(e))