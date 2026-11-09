import requests
import os

# Define endpoint
url = "http://127.0.0.1:8000/api/v1/analyze"

# File path
file_path = "backend/test/images/104655605.webp"
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

# Payload
files = {
    'file': ('image.webp', open(file_path, 'rb'), 'image/webp')
}
data = {
    'claim': 'This is a test claim for debugging 500 error',
    'enable_defense': 'false'
}

print(f"Sending POST request to {url}...")
try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text[:1000])  # Print first 1000 chars
except Exception as e:
    print(f"Request failed: {e}")
