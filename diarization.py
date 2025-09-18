import json
from io import BytesIO

import google.generativeai as genai
from fastapi import UploadFile
import uuid
from TranscriptionDto import TranscriptDTO
from mutagen.mp3 import MP3

import dynamoDb
from typing import Optional, List
from datetime import date

genai.configure(api_key="AIzaSyCKkmzhJq7dCGEq265ygUzsPawXROUtBZ4")
model = genai.GenerativeModel("gemini-1.5-flash")


def analyze_transcript(transcript_text: str):
  prompt = f"""
  I am providing you with a conversation between a customer and an agent. Based on the conversation, please provide a JSON object with the following parameters and data types: 
  - **agent_overall_rating:** An optional float representing the agent's overall performance rating from 1.0 to 5.0. 
  - **customer_sentiment_score:** An optional float representing the customer's sentiment score, with a higher number indicating a more positive sentiment. 
  - **conversation_quality_score:** An optional float representing the overall quality of the conversation, including clarity and flow. 
  - **agent_tone_score:** An optional float representing the agent's tone and politeness. 
  - **compliance_score:** An optional float representing how well the agent adhered to company policies and regulations. 
  - **responsiveness_score:** An optional float representing how quickly and effectively the agent responded to the customer's queries. 
  - **adaptability_score:** An optional float representing the agent's ability to adapt to the customer's needs and conversation flow. 
  - **product_awareness_score:** An optional float representing the agent's knowledge of the product or service discussed. 
  - **problem_resolution_score:** An optional float representing how effectively the agent resolved the customer's problem. 
  - **call_summarization:** An optional string providing a concise summary of the entire call. 
  - **actionable_insights:** An optional list of 2–3 short strings (max 2–3 lines total) suggesting specific actions the agent can take to improve performance and enhance business outcomes for real-estate listings and seeker/owner packages.

  {transcript_text}
  """

  response = model.generate_content(
    [
      {
        "role": "user",
        "parts": [
          {"text": prompt}
        ]
      }
    ],
    generation_config={"temperature": 0.2}
  )

  # The response text should contain your JSON
  return response.text


def get_mp3_duration(file_bytes: bytes) -> float:
  audio = MP3(BytesIO(file_bytes))
  return audio.info.length


def diarize_audio(audio_bytes: bytes, agent_id: int, customer_phone_number: str,
    s3_url: str, agent_name: str):
  genai.configure(api_key="AIzaSyAmubwjcP1LxKFEpFU0joUcKTZrVjcYb8A")
  print("Uploading start ")
  # 2. Choose a Gemini model that supports audio
  model = genai.GenerativeModel(
    "gemini-1.5-flash")  # or gemini-1.5-flash for cheaper/faster
  # file = genai.upload_file(path="audioFiles/output.wav")
  # call_id = 12345

  uploaded_file = genai.upload_file(
    BytesIO(audio_bytes),
    mime_type="audio/wav"  # or "audio/mpeg" if it's an mp3
  )
  print("Uploaded to GenAI:", uploaded_file)

  prompt = """
  You are a speaker diarization system. 
  Transcribe the audio and split it by speaker. 

  Map the speakers as follows:
  - Speaker 1 → agent
  - Speaker 2 → customer

  For each segment, provide:
  - speaker label (agent or customer)
  - start time
  - end time
  - spoken text

  Output strictly as JSON in an array of objects.
  """

  response = model.generate_content(
    [
      {"role": "user", "parts": [
        {"text": prompt},
        {"file_data": {
          "file_uri": uploaded_file.uri,
          "mime_type": "audio/wav"
        }}
      ]}
    ],
    generation_config={"temperature": 0.2}
  )

  print("diarization done: ", response.text)

  result = analyze_transcript(response.text)

  print("analyze_transcript done:", result)

  segment = dynamoDb.map_analysis_to_dto(
    transcript=response.text
    , agent_id=agent_id
    , customer_phone_number=customer_phone_number
    , audio_s3_path=s3_url
    , agent_name=agent_name
    , call_duration=get_mp3_duration(audio_bytes)
    , analysis_json=result
  )

  print("segment done")

  dynamoDb.insert_one(segment.dict())
  print(segment.dict())


def get_business_insights(date_param: Optional[date]):
  transcripts = dynamoDb.get_transcripts_by_date(date_param)
  print(transcripts)

  # Flatten all actionable_insights into one list
  all_insights: List[str] = []
  for entry in transcripts:
    if entry.get("actionable_insights"):
      all_insights.extend(entry["actionable_insights"])

  if not all_insights:
    return {"top_insights": []}
    
  print("top_insights :", all_insights)

  # --- Send to Gemini for summarization ---
  prompt = f"""
    I have the following actionable insights from multiple call transcripts:
    {json.dumps(all_insights, indent=2)}

    Please analyze them and return the top 5 most important and recurring insights 
    as a plain JSON list of strings, no extra text.
    """

  response = model.generate_content(prompt)

  try:
    top_insights = dynamoDb.safe_json_loads(response.text)
    if isinstance(top_insights, list):
      return top_insights
  except Exception:
    # Fallback: split into lines
    return [line.strip("-• ").strip() for line in response.text.split("\n") if
            line.strip()]

  return []