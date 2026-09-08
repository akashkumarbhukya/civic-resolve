import requests

# This is the URL where your Uvicorn server is listening
url = "http://127.0.0.1:8000/webhook"

# This is the exact JSON structure Meta/WhatsApp sends when a user types "HI"
whatsapp_payload = {
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "919876543210",
                    "type": "text",
                    "text": {"body": "HI"}
                }]
            }
        }]
    }]
}

print("Sending 'HI' to your webhook...")
response = requests.post(url, json=whatsapp_payload)
print(f"Webhook responded with: {response.text}")