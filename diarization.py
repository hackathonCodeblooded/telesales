import google.generativeai as genai

# 1. Configure Gemini
genai.configure(api_key="AIzaSyAmubwjcP1LxKFEpFU0joUcKTZrVjcYb8A")

# 2. Choose a Gemini model that supports audio
model = genai.GenerativeModel("gemini-1.5-flash")  # or gemini-1.5-flash for cheaper/faster

# 3. Load your audio
audio_file = genai.upload_file(path="audioFiles/output.wav")

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
    [prompt, audio_file],
    generation_config={"temperature": 0.2}
)

print(response.text)
