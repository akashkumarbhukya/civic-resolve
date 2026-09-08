import requests
import json

# These are provided by the Meta Developer Console when you create your app
ACCESS_TOKEN = "YOUR_META_ACCESS_TOKEN"
PHONE_NUMBER_ID = "YOUR_WHATSAPP_PHONE_NUMBER_ID"
VERSION = "v18.0" # Current Meta API version

def send_category_menu(recipient_phone: str):
    """
    Sends an interactive List Menu to the citizen asking for the issue category.
    """
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Meta's exact JSON structure for an Interactive List Message
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Civic Resolve 🏛️"
            },
            "body": {
                "text": "Welcome! What type of issue are you reporting today?"
            },
            "footer": {
                "text": "Your report helps improve the community."
            },
            "action": {
                "button": "Select Category",
                "sections": [
                    {
                        "title": "Public & Private Issues",
                        "rows": [
                            {
                                "id": "CAT_WASTE", 
                                "title": "🗑️ Waste & Sanitation",
                                "description": "Overflowing bins, illegal dumping"
                            },
                            {
                                "id": "CAT_ROADS", 
                                "title": "🚧 Roads & Streets",
                                "description": "Potholes, broken pavements"
                            },
                            {
                                "id": "CAT_WATER", 
                                "title": "💧 Water & Drainage",
                                "description": "Pipe leaks, clogged drains, flooding"
                            },
                            {
                                "id": "CAT_ELEC", 
                                "title": "⚡ Electricity",
                                "description": "Broken streetlamps, exposed wires"
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print(f"Successfully sent Category Menu to {recipient_phone}")
    else:
        print(f"Failed to send menu. Error: {response.text}")

    return response.json()

def send_property_type_menu(recipient_phone: str):
    """
    Sends interactive buttons asking if the issue is on Public or Private property.
    """
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
            "body": {
                "text": "Got it. Is this issue located on *Public Property* (e.g., main street) or *Private Property* (e.g., inside an apartment complex)?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "PROP_PUBLIC",
                            "title": "Public Property"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "PROP_PRIVATE",
                            "title": "Private Property"
                        }
                    }
                ]
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print(f"Successfully sent Property Type buttons to {recipient_phone}")
    else:
        print(f"Failed to send buttons. Error: {response.text}")

    return response.json()