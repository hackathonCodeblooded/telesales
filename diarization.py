import google.generativeai as genai
from fastapi import UploadFile
import uuid
from  TranscriptionDto import TranscriptDTO

import mongoConnection

def diarize_audio(file: UploadFile, call_id: int):
  genai.configure(api_key="AIzaSyAmubwjcP1LxKFEpFU0joUcKTZrVjcYb8A")

  # 2. Choose a Gemini model that supports audio
  model = genai.GenerativeModel("gemini-1.5-flash")  # or gemini-1.5-flash for cheaper/faster
  #file = genai.upload_file(path="audioFiles/output.wav")
  #call_id = 12345

  # 4. Send request with diarization instructions
  prompt = """
  You are a speaker diarization system. 
  Transcribe the audio and split by speaker (Speaker 1, Speaker 2, ...).
  For each segment, give:
  - speaker label
  - start time
  - end time
  - spoken text
  
  Output strictly as JSON in an array of objects.
  """

  response = model.generate_content(
      [prompt, file],
      generation_config={"temperature": 0.2}
  )

  segment = TranscriptDTO(
    call_id=call_id,
    transcript=response.text
  )

  mongoConnection.insert_one(segment.dict())
  print(segment.dict())

  print(response.text)