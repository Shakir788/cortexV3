import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WA_TOKEN = os.getenv("WA_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
RECIPIENT = os.getenv("RECIPIENT_PHONE")

print("Using PHONE_NUMBER_ID:", PHONE_NUMBER_ID)
print("Sending to:", RECIPIENT)

url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {WA_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "messaging_product": "whatsapp",
    "to": RECIPIENT,
    "type": "text",
    "text": {
        "body": "Hello Shakir bhai! 🚀 Ye message WhatsApp Cloud API se aaya hai."
    }
}

response = requests.post(url, headers=headers, json=payload)

print("Status:", response.status_code)
print("Response:", response.json())
