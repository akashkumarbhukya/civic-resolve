import os
import requests
import json

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN", "YOUR_META_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "YOUR_WHATSAPP_PHONE_NUMBER_ID")
VERSION = "v25.0"

def send_text_message(recipient_phone: str, text: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_main_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {"type": "text", "text": "Civic Resolve 🏛️"},
            "body": {"text": "Welcome to the Smart City portal. How can we help you today?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "BTN_REPORT", "title": "📢 Report Issue"}},
                    {"type": "reply", "reply": {"id": "BTN_JOIN_WORKFORCE", "title": "👷 Join Workforce"}}
                ]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_workforce_type_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Awesome! Are you registering to provide repair services (Technician) or to sell materials (Supplier)?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "BTN_TECH", "title": "🛠️ Technician"}},
                    {"type": "reply", "reply": {"id": "BTN_VENDOR", "title": "🏪 Supplier"}}
                ]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_tech_alert(recipient_phone: str, ticket_id: str, category: str, lat: str, lon: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": f"🚨 *NEW CIVIC JOB*\n\n🎫 ID: {ticket_id}\n⚠️ Issue: {category}\n📍 GPS: {lat}, {lon}\n\nFirst to accept claims the job!"},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": f"TACK_{ticket_id}", "title": "✅ Accept Job"}}]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_vendor_alert(recipient_phone: str, ticket_id: str, item_name: str, tech_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": f"🛒 *MATERIAL REQUIRED*\n\n🎫 Job: {ticket_id}\n🛠️ Item: {item_name}\n📞 Tech: {tech_phone}\n\nAccept to secure this sale!"},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": f"SACK_{ticket_id}", "title": "✅ Accept Order"}}]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_vendor_ready_button(recipient_phone: str, ticket_id: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "⏳ *TIME LIMIT ACTIVE*\n\nPlease prepare the goods immediately. Click the button below ONLY when the supplies are packed and ready for the technician to collect."},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": f"SDONE_{ticket_id}", "title": "📦 Supply is Ready"}}]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_category_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Issue Category"},
            "body": {"text": "What type of issue are you reporting today?"},
            "footer": {"text": "Select an option below"},
            "action": {
                "button": "Select Category",
                "sections": [{"title": "Categories", "rows": [
                    {"id": "CAT_WASTE", "title": "🗑️ Waste & Sanitation"},
                    {"id": "CAT_ROADS", "title": "🚧 Roads & Streets"},
                    {"id": "CAT_WATER", "title": "💧 Water & Drainage"},
                    {"id": "CAT_ELEC", "title": "⚡ Electricity"}
                ]}]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_property_type_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Is this issue located on *Public Property* or *Private Property*?"},
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
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "type": "interactive",
        "to": recipient_phone,
        "interactive": {
            "type": "location_request_message",
            "body": {"text": "📸 Photo received! Now, tap below to share the GPS location."},
            "action": {"name": "send_location"}
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_trade_skill_menu(recipient_phone: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Trade Specialization"},
            "body": {"text": "What is your primary area of expertise?"},
            "footer": {"text": "Select your trade skill"},
            "action": {
                "button": "Select Skill",
                "sections": [{"title": "Available Trades", "rows": [
                    {"id": "SKILL_ELEC", "title": "⚡ Electrician"},
                    {"id": "SKILL_PLUMB", "title": "💧 Plumber"},
                    {"id": "SKILL_ROADS", "title": "🚧 Roadworks / Mason"},
                    {"id": "SKILL_WASTE", "title": "🗑️ Waste Management"}
                ]}]
            }
        }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))