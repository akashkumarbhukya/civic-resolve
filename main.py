import os
import sqlite3
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from database import init_db
from whatsapp_api import send_category_menu, send_property_type_menu, send_text_message, send_location_request, send_trade_skill_menu

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "sih_civic_resolve_2026")
user_sessions = {}

def update_worker_location(phone, new_pincode):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE workforce SET pincode = ? WHERE phone_number = ?", (new_pincode, phone))
    conn.commit()
    conn.close()

def notify_workers(ticket_id, lat, lon):
    """Fetches all active workers from the DB and sends them an alert."""
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number FROM workforce WHERE status = 'ACTIVE'")
    workers = cursor.fetchall()
    conn.close()

    alert_message = (
        "🚨 *NEW CIVIC TICKET DISPATCHED*\n\n"
        f"🎫 Ticket ID: {ticket_id}\n"
        f"📍 Location Coordinates: {lat}, {lon}\n\n"
        "Please check the portal to accept this task."
    )
    
    for worker in workers:
        worker_phone = worker[0]
        if not worker_phone.startswith("91"):
            worker_phone = "91" + worker_phone
        send_text_message(worker_phone, alert_message)

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("SELECT worker_id, govt_emp_id, name, phone_number, worker_type, pincode, status FROM workforce")
    workers = cursor.fetchall()
    conn.close()

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Civic Resolve - Admin Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
            h2, h3 { color: #333; }
            table { width: 100%; border-collapse: collapse; background: #fff; margin-bottom: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
            th { background: #007bff; color: white; }
            form { background: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 600px; }
            input, select { width: 100%; padding: 8px; margin: 8px 0 15px 0; display: inline-block; border: 1px solid #ccc; box-sizing: border-box; }
            button { background: #28a745; color: white; padding: 10px 15px; border: none; cursor: pointer; width: 100%; }
            button:hover { background: #218838; }
            .delete-btn { background: #dc3545; padding: 5px 10px; width: auto; }
            .delete-btn:hover { background: #c82333; }
        </style>
    </head>
    <body>
        <h2>🏛️ Civic Resolve - Official Workforce Admin Panel</h2>
        
        <h3>Current Workforce Directory</h3>
        <table>
            <tr>
                <th>ID / Emp ID</th>
                <th>Name</th>
                <th>Phone Number</th>
                <th>Type</th>
                <th>Pincode</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
    """
    for w in workers:
        html_content += f"""
            <tr>
                <td>{w[0]} ({w[1] if w[1] else 'N/A'})</td>
                <td>{w[2]}</td>
                <td>{w[3]}</td>
                <td>{w[4]}</td>
                <td>{w[5]}</td>
                <td>{w[6]}</td>
                <td>
                    <form action="/admin/delete/{w[0]}" method="post" style="padding:0; box-shadow:none;">
                        <button type="submit" class="delete-btn">Delete</button>
                    </form>
                </td>
            </tr>
        """

    html_content += """
        </table>

        <h3>Add New Worker</h3>
        <form action="/admin/add" method="post">
            <label>Name:</label>
            <input type="text" name="name" required>
            
            <label>Phone Number:</label>
            <input type="text" name="phone_number" required>
            
            <label>Worker Type:</label>
            <select name="worker_type">
                <option value="GOVT">GOVT</option>
                <option value="PRIVATE_TECH">PRIVATE_TECH</option>
                <option value="VENDOR">VENDOR</option>
            </select>
            
            <label>Govt Emp ID (Optional):</label>
            <input type="text" name="govt_emp_id">
            
            <label>Pincode:</label>
            <input type="text" name="pincode" value="506134" required>
            
            <button type="submit">Add Worker</button>
        </form>
    </body>
    </html>
    """
    return html_content

@app.post("/admin/add")
async def add_worker(name: str = Form(...), phone_number: str = Form(...), worker_type: str = Form(...), govt_emp_id: str = Form(None), pincode: str = Form(...)):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO workforce (phone_number, worker_type, trade_skill, pincode, status, govt_emp_id, name)
        VALUES (?, ?, 'GENERAL_CIVIC', ?, 'ACTIVE', ?, ?)
        ''', (phone_number, worker_type, pincode, govt_emp_id if govt_emp_id else None, name))
        conn.commit()
    except Exception as e:
        print(f"Error adding worker: {e}")
    finally:
        conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/admin/delete/{worker_id}")
async def delete_worker(worker_id: int):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workforce WHERE worker_id = ?", (worker_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        if challenge:
            return int(challenge)
    return {"status": "error", "message": "Verification failed"}

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    body = await request.json()
    try:
        entry = body['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            message_data = entry['messages'][0]
            sender_phone = message_data['from']
            message_type = message_data['type']
            
            # Safely initialize session memory so it doesn't crash between messages
            if sender_phone not in user_sessions:
                user_sessions[sender_phone] = {}
            session = user_sessions[sender_phone]
            
            # --- 1. HANDLE TEXT MESSAGES ---
            if message_type == 'text':
                text_received = message_data['text']['body'].upper().strip()
                
                if text_received in ["HI", "HELLO"]:
                    user_sessions[sender_phone] = {"step": "category_selection"}
                    send_category_menu(sender_phone)
                    
                elif text_received == "JOIN":
                    # SKIP the Govt/Private menu! Default to Private Tech and immediately ask for skills.
                    user_sessions[sender_phone] = {
                        "step": "trade_skill_selection",
                        "worker_type": "PRIVATE_TECH"
                    }
                    send_trade_skill_menu(sender_phone)
                    
                # Handle Pincode input during worker registration
                elif session.get("step") == "awaiting_pincode":
                    user_sessions[sender_phone]["pincode"] = text_received
                    user_sessions[sender_phone]["step"] = "awaiting_id_photo"
                    send_text_message(sender_phone, "📸 Please upload a photo of your Government ID (PAN/Trade License) for verification.")
                    
            # --- 2. HANDLE INTERACTIVE BUTTONS/LISTS ---
            elif message_type == 'interactive':
                interactive_data = message_data['interactive']
                
                if interactive_data['type'] == 'list_reply':
                    selected_id = interactive_data['list_reply']['id']
                    
                    # Citizen Category Selection
                    if selected_id in ["CAT_WASTE", "CAT_ROADS", "CAT_WATER", "CAT_ELEC"]:
                        user_sessions[sender_phone]["category"] = selected_id
                        send_property_type_menu(sender_phone)
                        
                    # Worker Trade Skill Selection
                    elif selected_id in ["SKILL_ELEC", "SKILL_PLUMB", "SKILL_ROADS", "SKILL_WASTE"]:
                        user_sessions[sender_phone]["trade_skill"] = selected_id
                        user_sessions[sender_phone]["step"] = "awaiting_pincode"
                        send_text_message(sender_phone, "📍 Please reply with the 6-digit Pincode of your primary operating area (e.g., 506134).")
                        
                elif interactive_data['type'] == 'button_reply':
                    selected_id = interactive_data['button_reply']['id']
                    
                    # Citizen Property Selection
                    if selected_id in ["PROP_PUBLIC", "PROP_PRIVATE"]:
                        user_sessions[sender_phone]["step"] = "awaiting_issue_photo"
                        send_text_message(sender_phone, "📸 Please upload a clear photo of the issue so we can assess the damage.")

            # --- 3. HANDLE PHOTO UPLOADS ---
            elif message_type == 'image':
                # If Citizen is uploading an issue photo
                if session.get("step") == "awaiting_issue_photo":
                    send_location_request(sender_phone)
                    
                # If Worker is uploading ID proof
                elif session.get("step") == "awaiting_id_photo":
                    worker_type = session.get("worker_type", "PRIVATE_TECH")
                    trade_skill = session.get("trade_skill", "GENERAL")
                    pincode = session.get("pincode", "000000")
                    
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT OR IGNORE INTO workforce (phone_number, worker_type, trade_skill, pincode, status, name)
                    VALUES (?, ?, ?, ?, 'PENDING_REVIEW', ?)
                    ''', (sender_phone, worker_type, trade_skill, pincode, "New Applicant"))
                    conn.commit()
                    conn.close()
                    
                    worker_id = f"PT-{random.randint(1000, 9999)}"
                    send_text_message(sender_phone, f"✅ Registration complete! Your application is under review.\n🆔 Temporary ID: {worker_id}\n\nWe will notify you here once you are approved to receive local service requests.")
                    user_sessions.pop(sender_phone, None)

            # --- 4. HANDLE LOCATION & FINALIZE CITIZEN TICKET ---
            elif message_type == 'location':
                lat = message_data['location']['latitude']
                lon = message_data['location']['longitude']
                
                ticket_id = f"CR-{random.randint(1000, 9999)}"
                clean_msg = (
                    "✅ *Ticket registered successfully!*\n"
                    "📍 Location secured.\n"
                    f"🎫 Ticket ID: {ticket_id}\n\n"
                    "👷 A verified technician has been dispatched to your location. "
                    "Track your status anytime by replying 'Status'."
                )
                send_text_message(sender_phone, clean_msg)
                notify_workers(ticket_id, lat, lon)

        return {"status": "success"}
    except Exception as e:
        import traceback
        print(f"Webhook error: {e}")
        traceback.print_exc()
        return {"status": "error"}