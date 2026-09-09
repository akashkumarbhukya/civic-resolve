import os
import requests
import json

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN", "YOUR_META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "YOUR_WHATSAPP_PHONE_NUMBER_ID")
VERSION = "v25.0"

def send_text_message(recipient_phone: str, text: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

def send_category_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Civic Resolve 🏛️"},
            "body": {"text": "Welcome! What type of issue are you reporting today?"},
            "footer": {"text": "Your report helps improve the community."},
            "action": {
                "button": "Select Category",
                "sections": [
                    {
                        "title": "Public & Private Issues",
                        "rows": [
                            {"id": "CAT_WASTE", "title": "🗑️ Waste & Sanitation", "description": "Overflowing bins, dumping"},
                            {"id": "CAT_ROADS", "title": "🚧 Roads & Streets", "description": "Potholes, broken pavements"},
                            {"id": "CAT_WATER", "title": "💧 Water & Drainage", "description": "Pipe leaks, flooding"},
                            {"id": "CAT_ELEC", "title": "⚡ Electricity", "description": "Broken streetlamps, wires"}
                        ]
                    }
                ]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_property_type_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Got it. Is this issue located on *Public Property* or *Private Property*?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "PROP_PUBLIC", "title": "Public Property"}},
                    {"type": "reply", "reply": {"id": "PROP_PRIVATE", "title": "Private Property"}}
                ]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_location_request(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "interactive",
        "to": recipient_phone,
        "interactive": {
            "type": "location_request_message",
            "body": {
                "text": "📸 Photo received! Now, please tap the button below to securely share the exact GPS location of the issue."
            },
            "action": {
                "name": "send_location"
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))