import requests

url = "http://127.0.0.1:8000/upload-audio"
file_path = "sample.wav"

with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "audio/wav")}
    data = {
        "agent_id": "12345",
        "customer_phone_number": "9876543210"
    }
    response = requests.post(url, files=files, data=data)

print(response.status_code)
print(response.json())
