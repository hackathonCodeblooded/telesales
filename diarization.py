from io import BytesIO

import google.generativeai as genai
from fastapi import UploadFile
import uuid
from  TranscriptionDto import TranscriptDTO
from mutagen.mp3 import MP3

import dynamoDb

def get_mp3_duration(file_bytes: bytes) -> float:
    audio = MP3(BytesIO(file_bytes))
    return audio.info.length

def diarize_audio(audio_bytes: bytes, agent_id: str, customer_phone_number: str, s3_url: str, agent_name: str):
  genai.configure(api_key="AIzaSyAmubwjcP1LxKFEpFU0joUcKTZrVjcYb8A")
  print("Uploading start ")
  # 2. Choose a Gemini model that supports audio
  model = genai.GenerativeModel("gemini-1.5-flash")  # or gemini-1.5-flash for cheaper/faster
  #file = genai.upload_file(path="audioFiles/output.wav")
  #call_id = 12345

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



  segment = TranscriptDTO(
    transcript=response.text
    , agent_id=agent_id
    , customer_phone_number=customer_phone_number
    , audio_s3_path=s3_url
    , agent_name=agent_name
    , call_duration=get_mp3_duration(audio_bytes)
  )

  dynamoDb.insert_one(segment.dict())
  print(segment.dict())

  print(response.text)