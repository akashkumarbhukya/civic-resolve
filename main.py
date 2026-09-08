from fastapi import FastAPI, Request
import sqlite3

# Cleaned up imports
from whatsapp_api import send_category_menu, send_property_type_menu

app = FastAPI()

VERIFY_TOKEN = "sih_civic_resolve_2026"

# Temporary memory to store what category a user selected
user_sessions = {}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    This endpoint is used by Meta/WhatsApp to verify your server is real.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"status": "error", "message": "Verification failed"}

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """
    This is where all incoming WhatsApp messages arrive.
    """
    body = await request.json()
    
    try:
        entry = body['entry'][0]['changes'][0]['value']
        
        if 'messages' in entry:
            message_data = entry['messages'][0]
            sender_phone = message_data['from']
            message_type = message_data['type']
            
            # ---------------------------------------------------------
            # SCENARIO 1: TEXT MESSAGES
            # ---------------------------------------------------------
            if message_type == 'text':
                text_received = message_data['text']['body'].upper().strip()
                
                if text_received == "HI":
                    print(f"New user {sender_phone} said Hi. Sending Category Menu...")
                    # Initialize their session
                    user_sessions[sender_phone] = {"step": "category_selection"}
                    send_category_menu(sender_phone)
                
                elif text_received == "JOIN":
                    print(f"Worker {sender_phone} wants to join.")
                    
                elif text_received.startswith("UPDATE PINCODE"):
                    new_pincode = text_received.split(" ")[2]
                    update_worker_location(sender_phone, new_pincode)
                    print(f"Updated worker {sender_phone} to new pincode {new_pincode}")

            # ---------------------------------------------------------
            # SCENARIO 2: INTERACTIVE BUTTON CLICKS
            # ---------------------------------------------------------
            elif message_type == 'interactive':
                interactive_data = message_data['interactive']
                
                # Check if they tapped an item from the Category List
                if interactive_data['type'] == 'list_reply':
                    selected_id = interactive_data['list_reply']['id']
                    
                    if selected_id in ["CAT_WASTE", "CAT_ROADS", "CAT_WATER", "CAT_ELEC"]:
                        print(f"User {sender_phone} selected {selected_id}.")
                        
                        # Save their selection in memory
                        if sender_phone not in user_sessions:
                            user_sessions[sender_phone] = {}
                        user_sessions[sender_phone]["category"] = selected_id
                        
                        # Ask the next question
                        send_property_type_menu(sender_phone)

                # Check if they tapped the Public/Private Reply Button
                elif interactive_data['type'] == 'button_reply':
                    button_id = interactive_data['button_reply']['id']
                    
                    if button_id in ["PROP_PUBLIC", "PROP_PRIVATE"]:
                        print(f"User {sender_phone} chose {button_id}.")
                        
                        # Save property type to memory
                        if sender_phone in user_sessions:
                            user_sessions[sender_phone]["property_type"] = button_id
                            # Here you would trigger the Location Request step next
                            print(f"Current Session Data for {sender_phone}: {user_sessions[sender_phone]}")

            # ---------------------------------------------------------
            # SCENARIO 3: GPS LOCATION
            # ---------------------------------------------------------
            elif message_type == 'location':
                latitude = message_data['location']['latitude']
                longitude = message_data['location']['longitude']
                print(f"Received location from {sender_phone}: Lat {latitude}, Lon {longitude}")
                
            # ---------------------------------------------------------
            # SCENARIO 4: IMAGE UPLOAD
            # ---------------------------------------------------------
            elif message_type == 'image':
                image_id = message_data['image']['id']
                print(f"Received image ID {image_id} from {sender_phone}")

        return {"status": "success"}
        
    except Exception as e:
        print(f"Error processing message: {e}")
        return {"status": "error"}

def update_worker_location(phone, new_pincode):
    """Function to allow private workers to change locations seamlessly"""
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE workforce SET pincode = ? WHERE phone_number = ?", (new_pincode, phone))
    conn.commit()
    conn.close()