import os
import sqlite3
import random
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from database import init_db
from whatsapp_api import (
    send_main_menu, send_workforce_type_menu, send_category_menu, 
    send_property_type_menu, send_text_message, send_location_request, 
    send_trade_skill_menu, send_tech_alert, send_vendor_alert, 
    send_vendor_ready_button
)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "sih_civic_resolve_2026")
user_sessions = {}

# --- PROACTIVE BACKGROUND TIMEOUT TASK ---
async def session_timeout_checker():
    """Runs in the background to proactively message users who timeout."""
    while True:
        await asyncio.sleep(60) # Check every 60 seconds
        current_time = time.time()
        expired_users = []
        
        # Safely iterate over a list of items to avoid dict changing size
        for phone, session in list(user_sessions.items()):
            if current_time - session.get("last_activity", current_time) > 300: # 5 Minutes
                expired_users.append(phone)
                
        for phone in expired_users:
            send_text_message(phone, "⏳ Session timed out due to inactivity. Please send 'Hi' to restart.")
            user_sessions.pop(phone, None)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start the proactive timeout checker when the server boots
    task = asyncio.create_task(session_timeout_checker())
    yield
    task.cancel() # Stop the task if the server shuts down

app = FastAPI(lifespan=lifespan)

# --- WORKER ALERTS ---
def broadcast_to_techs(ticket_id, category, lat, lon):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number FROM workforce WHERE status = 'ACTIVE' AND worker_type IN ('GOVT', 'PRIVATE_TECH')")
    workers = cursor.fetchall()
    conn.close()
    for worker in workers:
        worker_phone = worker[0]
        if not worker_phone.startswith("91"): worker_phone = "91" + worker_phone
        send_tech_alert(worker_phone, ticket_id, category, lat, lon)

def broadcast_to_vendors(ticket_id, item_name, tech_phone):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone_number FROM workforce WHERE worker_type = 'VENDOR' AND status = 'ACTIVE'")
    vendors = cursor.fetchall()
    conn.close()
    for vendor in vendors:
        v_phone = vendor[0]
        if not v_phone.startswith("91"): v_phone = "91" + v_phone
        send_vendor_alert(v_phone, ticket_id, item_name, tech_phone)

# --- ADMIN DASHBOARD ---
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    # Sorts the database so identical Pincodes are grouped together!
    cursor.execute("SELECT worker_id, govt_emp_id, name, phone_number, worker_type, pincode, status FROM workforce ORDER BY pincode ASC, worker_type ASC")
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
            .update-btn { background: #ffc107; color: black; padding: 5px 10px; width: auto; margin-right: 5px; }
            .update-btn:hover { background: #e0a800; }
            .delete-btn { background: #dc3545; padding: 5px 10px; width: auto; }
            .delete-btn:hover { background: #c82333; }
            .inline-input { width: 110px; padding: 5px; margin: 0; }
        </style>
    </head>
    <body>
        <h2>🏛️ Civic Resolve - Official Workforce Admin Panel</h2>
        
        <h3>Current Workforce Directory (Grouped by Pincode)</h3>
        <table>
            <tr>
                <th>ID / Emp ID</th>
                <th>Name</th>
                <th>Phone Number (Edit)</th>
                <th>Type</th>
                <th>Pincode (Edit)</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
    """
    for w in workers:
        html_content += f"""
            <tr>
                <td>{w[0]} ({w[1] if w[1] else 'N/A'})</td>
                <td>{w[2]}</td>
                <form action="/admin/update/{w[0]}" method="post" style="padding:0; box-shadow:none; margin:0; background:transparent;">
                    <td><input type="text" name="phone_number" value="{w[3]}" class="inline-input"></td>
                    <td>{w[4]}</td>
                    <td><input type="text" name="pincode" value="{w[5]}" class="inline-input"></td>
                    <td>{w[6]}</td>
                    <td>
                        <button type="submit" class="update-btn">Update</button>
                </form>
                <form action="/admin/delete/{w[0]}" method="post" style="display:inline; padding:0; box-shadow:none; margin:0; background:transparent;">
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

@app.post("/admin/update/{worker_id}")
async def update_worker(worker_id: int, phone_number: str = Form(...), pincode: str = Form(...)):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE workforce SET phone_number = ?, pincode = ? WHERE worker_id = ?", (phone_number, pincode, worker_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/admin/add")
async def add_worker(name: str = Form(...), phone_number: str = Form(...), worker_type: str = Form(...), govt_emp_id: str = Form(None), pincode: str = Form(...)):
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO workforce (phone_number, worker_type, trade_skill, pincode, status, govt_emp_id, name)
    VALUES (?, ?, 'GENERAL_CIVIC', ?, 'ACTIVE', ?, ?)
    ''', (phone_number, worker_type, pincode, govt_emp_id if govt_emp_id else None, name))
    conn.commit()
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

# --- WHATSAPP WEBHOOK ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
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
            
            # Restart session safely and update timestamp
            if sender_phone not in user_sessions:
                user_sessions[sender_phone] = {}
            session = user_sessions[sender_phone]
            session["last_activity"] = time.time()
            
            # --- 2. HANDLE TEXT MESSAGES ---
            if message_type == 'text':
                text_received = message_data['text']['body'].upper().strip()
                
                # Main Menu (Case Insensitive + Handles multiple trigger words)
                if text_received in ["HI", "HELLO", "START", "MENU", "HEY", "JOIN"]:
                    send_main_menu(sender_phone)
                    user_sessions.pop(sender_phone, None) 
                    
                # GOVT OTP APPROVAL LOGIC
                elif text_received.startswith("APPROVE "):
                    otp = text_received[8:].strip()
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    
                    # Verify sender is a Govt Employee
                    cursor.execute("SELECT worker_type FROM workforce WHERE phone_number = ?", (sender_phone,))
                    sender_role = cursor.fetchone()
                    
                    if sender_role and sender_role[0] == 'GOVT':
                        # Find the Private user with this OTP
                        cursor.execute("SELECT phone_number, otp_expiry FROM workforce WHERE otp = ? AND status = 'PENDING_APPROVAL'", (otp,))
                        target = cursor.fetchone()
                        
                        if target:
                            if time.time() < target[1]: # Check if 10 mins passed
                                cursor.execute("UPDATE workforce SET status = 'ACTIVE', otp = NULL, otp_expiry = NULL WHERE phone_number = ?", (target[0],))
                                conn.commit()
                                send_text_message(sender_phone, f"✅ Worker (+{target[0]}) successfully authorized and activated!")
                                send_text_message(target[0], "🎉 Your profile has been approved by a Government Official. You are now active in the workforce system!")
                            else:
                                send_text_message(sender_phone, "⚠️ This OTP has expired (validity is 10 minutes). They must register again.")
                        else:
                            send_text_message(sender_phone, "🚫 Invalid OTP or user is already activated.")
                    else:
                        send_text_message(sender_phone, "🚫 Unauthorized. Only Government Officials can approve new workers.")
                    conn.close()

                # PROCUREMENT REQUEST
                elif text_received.startswith("NEED "):
                    item = text_received[5:].strip()
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT ticket_id FROM tickets WHERE assigned_worker_phone = ? AND status = 'ASSIGNED' ORDER BY created_at DESC LIMIT 1", (sender_phone,))
                    row = cursor.fetchone()
                    
                    if row:
                        ticket_id = row[0]
                        cursor.execute("UPDATE tickets SET material_requested = ?, material_status = 'REQUESTED' WHERE ticket_id = ?", (item, ticket_id))
                        conn.commit()
                        broadcast_to_vendors(ticket_id, item, sender_phone)
                        send_text_message(sender_phone, f"✅ Order for '{item}' broadcasted to local suppliers. We will alert you when a shop accepts.")
                    else:
                        send_text_message(sender_phone, "⚠️ You must claim a job before requesting materials.")
                    conn.close()
                
                # RESOLUTION
                elif text_received.startswith("RESOLVED "):
                    ticket_id = text_received[9:].strip().upper()
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT assigned_worker_phone FROM tickets WHERE ticket_id = ?", (ticket_id,))
                    row = cursor.fetchone()
                    
                    if row and row[0] == sender_phone:
                        cursor.execute("UPDATE tickets SET status = 'RESOLVED' WHERE ticket_id = ?", (ticket_id,))
                        conn.commit()
                        user_sessions[sender_phone]["step"] = "awaiting_after_photo"
                        user_sessions[sender_phone]["current_ticket"] = ticket_id
                        send_text_message(sender_phone, f"✅ {ticket_id} marked RESOLVED.\n\n📸 Please upload a clear 'After' photo of the fixed issue.")
                    else:
                        send_text_message(sender_phone, "🚫 Unauthorized. Only the assigned technician can close this ticket.")
                    conn.close()
                    
                # Pincode capture for Workforce Registration
                elif session.get("step") == "awaiting_pincode":
                    user_sessions[sender_phone]["pincode"] = text_received
                    user_sessions[sender_phone]["step"] = "awaiting_id_photo"
                    send_text_message(sender_phone, "📸 Please upload a photo of your Government ID/Trade License for verification.")
                    
                # Rating logic
                elif session.get("step") == "awaiting_rating":
                    if text_received in ["1", "2", "3", "4", "5"]:
                        ticket_id = session.get("current_ticket", "")
                        send_text_message(sender_phone, f"🙏 Rating {text_received}⭐ recorded. Have a great day!")
                        user_sessions.pop(sender_phone, None)
                    else:
                        send_text_message(sender_phone, "Please reply with a number from 1 to 5.")
                        
            # --- 3. HANDLE INTERACTIVE BUTTONS/LISTS ---
            elif message_type == 'interactive':
                interactive_data = message_data['interactive']
                
                # LIST RESPONSES
                if interactive_data['type'] == 'list_reply':
                    selected_id = interactive_data['list_reply']['id']
                    
                    if selected_id in ["CAT_WASTE", "CAT_ROADS", "CAT_WATER", "CAT_ELEC"]:
                        user_sessions[sender_phone]["category"] = selected_id
                        send_property_type_menu(sender_phone)
                        
                    elif selected_id in ["SKILL_ELEC", "SKILL_PLUMB", "SKILL_ROADS", "SKILL_WASTE"]:
                        user_sessions[sender_phone]["trade_skill"] = selected_id
                        user_sessions[sender_phone]["step"] = "awaiting_pincode"
                        send_text_message(sender_phone, "📍 Reply with your 6-digit Pincode (e.g., 506134).")
                        
                # BUTTON RESPONSES
                elif interactive_data['type'] == 'button_reply':
                    selected_id = interactive_data['button_reply']['id']
                    
                    # Nested Main Menu Logic
                    if selected_id == "BTN_REPORT":
                        user_sessions[sender_phone]["step"] = "category_selection"
                        send_category_menu(sender_phone)
                    elif selected_id == "BTN_JOIN_WORKFORCE":
                        user_sessions[sender_phone]["step"] = "workforce_type_selection"
                        send_workforce_type_menu(sender_phone)
                        
                    # Workforce Type Selection
                    elif selected_id == "BTN_TECH":
                        user_sessions[sender_phone] = {"step": "trade_skill_selection", "worker_type": "PRIVATE_TECH"}
                        send_trade_skill_menu(sender_phone)
                    elif selected_id == "BTN_VENDOR":
                        user_sessions[sender_phone] = {"step": "awaiting_pincode", "worker_type": "VENDOR", "trade_skill": "SUPPLIER"}
                        send_text_message(sender_phone, "🏪 Welcome, Supplier! 📍 Reply with your 6-digit Shop Pincode (e.g., 506134).")
                        
                    # Citizen Property Selection
                    elif selected_id in ["PROP_PUBLIC", "PROP_PRIVATE"]:
                        user_sessions[sender_phone]["property_type"] = "PUBLIC" if selected_id == "PROP_PUBLIC" else "PRIVATE"
                        user_sessions[sender_phone]["step"] = "awaiting_issue_photo"
                        send_text_message(sender_phone, "📸 Please upload a clear photo of the issue.")

                    # TECH CLAIMS TICKET (Concurrency Locked)
                    elif selected_id.startswith("TACK_"):
                        ticket_id = selected_id.split("_")[1]
                        conn = sqlite3.connect('civic_resolve.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT assigned_worker_phone, latitude, longitude FROM tickets WHERE ticket_id = ?", (ticket_id,))
                        row = cursor.fetchone()
                        
                        if row and row[0]: # Already assigned
                            if row[0] == sender_phone:
                                send_text_message(sender_phone, "⚠️ You have already claimed this job.")
                            else:
                                send_text_message(sender_phone, "🔒 Sorry, another technician was faster and claimed this job.")
                        else:
                            cursor.execute("UPDATE tickets SET assigned_worker_phone = ?, status = 'ASSIGNED' WHERE ticket_id = ?", (sender_phone, ticket_id))
                            conn.commit()
                            maps_url = f"https://maps.google.com/?q={row[1]},{row[2]}"
                            send_text_message(sender_phone, f"✅ Job Claimed!\n\n📍 Google Maps Route: {maps_url}\n\nNeed parts? Text 'NEED [item]'.\nDone? Text 'RESOLVED {ticket_id}'.")
                        conn.close()

                    # VENDOR CLAIMS SUPPLY ORDER (Concurrency Locked)
                    elif selected_id.startswith("SACK_"):
                        ticket_id = selected_id.split("_")[1]
                        conn = sqlite3.connect('civic_resolve.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT vendor_phone, material_requested, assigned_worker_phone FROM tickets WHERE ticket_id = ?", (ticket_id,))
                        row = cursor.fetchone()
                        
                        if row and row[0]: # Already assigned
                            send_text_message(sender_phone, "🔒 Sorry, another supplier already accepted this order.")
                        else:
                            cursor.execute("UPDATE tickets SET vendor_phone = ?, material_status = 'ACCEPTED' WHERE ticket_id = ?", (sender_phone, ticket_id))
                            conn.commit()
                            send_vendor_ready_button(sender_phone, ticket_id)
                            send_text_message(row[2], f"✅ A local shop (+{sender_phone}) has accepted your order for '{row[1]}'. We will text you when it is ready for pickup!")
                        conn.close()

                    # VENDOR HITS "SUPPLY READY"
                    elif selected_id.startswith("SDONE_"):
                        ticket_id = selected_id.split("_")[1]
                        conn = sqlite3.connect('civic_resolve.db')
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tickets SET material_status = 'SUPPLIED' WHERE ticket_id = ?", (ticket_id,))
                        conn.commit()
                        
                        cursor.execute("SELECT assigned_worker_phone, property_type FROM tickets WHERE ticket_id = ?", (ticket_id,))
                        tech_phone, prop_type = cursor.fetchone()
                        conn.close()
                        
                        send_text_message(sender_phone, "✅ Thank you! The technician has been notified to pick up the materials.")
                        
                        if prop_type == "PUBLIC":
                            user_sessions[tech_phone] = {"step": "awaiting_bill_photo", "current_ticket": ticket_id}
                            send_text_message(tech_phone, f"📦 Materials are ready for pickup at supplier shop (+{sender_phone})!\n\n🏛️ Since this is a PUBLIC job, please upload a photo of the shop's BILL for municipal reimbursement.")
                        else:
                            send_text_message(tech_phone, f"📦 Materials are ready for pickup at supplier shop (+{sender_phone})!\n\n💳 Since this is a PRIVATE job, please settle the cost directly with the shop and citizen.")

            # --- 4. HANDLE PHOTO UPLOADS ---
            elif message_type == 'image':
                if session.get("step") == "awaiting_issue_photo":
                    send_location_request(sender_phone)
                    
                # Tech uploads the Supply Bill
                elif session.get("step") == "awaiting_bill_photo":
                    send_text_message(sender_phone, "🧾 Bill securely uploaded for municipal reimbursement! Proceed with the fix and text 'RESOLVED [ID]' when finished.")
                    user_sessions.pop(sender_phone, None)
                    
                # PRIVATE WORKER OTP REGISTRATION LOGIC
                elif session.get("step") == "awaiting_id_photo":
                    worker_type = session.get("worker_type", "PRIVATE_TECH")
                    trade_skill = session.get("trade_skill", "GENERAL")
                    pincode = session.get("pincode", "000000")
                    
                    # Generate 6 digit OTP and 10 minute expiry timestamp
                    otp_code = str(random.randint(100000, 999999))
                    expiry_time = time.time() + 600
                    
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT OR IGNORE INTO workforce (phone_number, worker_type, trade_skill, pincode, status, name, otp, otp_expiry)
                    VALUES (?, ?, ?, ?, 'PENDING_APPROVAL', ?, ?, ?)
                    ''', (sender_phone, worker_type, trade_skill, pincode, "New User", otp_code, expiry_time))
                    conn.commit()
                    conn.close()
                    
                    send_text_message(sender_phone, f"⏳ *Action Required!*\n\nYour profile has been created. To activate it, please show this code to an official Government Employee:\n\n🔢 *{otp_code}*\n\n(This code expires in 10 minutes).")
                    user_sessions.pop(sender_phone, None)
                    
                # Final After Photo
                elif session.get("step") == "awaiting_after_photo":
                    ticket_id = session.get("current_ticket", "")
                    send_text_message(sender_phone, f"🏆 'After' photo successfully saved for {ticket_id}!\nThe civic loop is now closed. Great work today!")
                    user_sessions.pop(sender_phone, None)
                    
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT citizen_phone, property_type FROM tickets WHERE ticket_id = ?", (ticket_id,))
                    ticket_info = cursor.fetchone()
                    conn.close()
                    
                    if ticket_info:
                        citizen_phone = ticket_info[0]
                        property_type = ticket_info[1]
                        msg = f"✅ *TICKET RESOLVED: {ticket_id}*\n\nYour reported issue has been fixed!"
                        if property_type == "PRIVATE": msg += "\n\n💳 *Payment:* Please coordinate payment directly with the tech offline."
                        else: msg += "\n\n🏛️ *Payment:* Covered by municipal services. No payment required."
                        msg += "\n\n⭐ *Feedback:* Reply with a number 1 to 5 to rate the service."
                        
                        send_text_message(citizen_phone, msg)
                        user_sessions[citizen_phone] = {"step": "awaiting_rating", "current_ticket": ticket_id, "last_activity": time.time()}

            # --- 5. HANDLE LOCATION ---
            elif message_type == 'location':
                if session.get("step") == "awaiting_issue_photo" or session.get("category"):
                    lat = message_data['location']['latitude']
                    lon = message_data['location']['longitude']
                    category = session.get("category", "GENERAL")
                    property_type = session.get("property_type", "PUBLIC")
                    ticket_id = f"CR-{random.randint(1000, 9999)}"
                    
                    conn = sqlite3.connect('civic_resolve.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT INTO tickets (ticket_id, citizen_phone, category, property_type, latitude, longitude, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
                    ''', (ticket_id, sender_phone, category, property_type, str(lat), str(lon)))
                    conn.commit()
                    conn.close()
                    
                    send_text_message(sender_phone, f"✅ *Ticket registered!*\n🎫 ID: {ticket_id}\n\n👷 A tech alert has been dispatched.")
                    broadcast_to_techs(ticket_id, category, lat, lon)
                    user_sessions.pop(sender_phone, None)

        return {"status": "success"}
    except Exception as e:
        import traceback
        print(f"Webhook error: {e}")
        traceback.print_exc()
        return {"status": "error"}