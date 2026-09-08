import os
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from database import init_db
from whatsapp_api import send_category_menu, send_property_type_menu, send_text_message

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
            
            if message_type == 'text':
                text_received = message_data['text']['body'].upper().strip()
                if text_received in ["HI", "HELLO"]:
                    user_sessions[sender_phone] = {"step": "category_selection"}
                    send_category_menu(sender_phone)
                elif text_received == "JOIN":
                    send_text_message(sender_phone, "To join the workforce, please register through the admin portal.")
                    
            elif message_type == 'interactive':
                interactive_data = message_data['interactive']
                if interactive_data['type'] == 'list_reply':
                    selected_id = interactive_data['list_reply']['id']
                    if selected_id in ["CAT_WASTE", "CAT_ROADS", "CAT_WATER", "CAT_ELEC"]:
                        user_sessions[sender_phone] = {"category": selected_id}
                        send_property_type_menu(sender_phone)
                elif interactive_data['type'] == 'button_reply':
                    if interactive_data['button_reply']['id'] in ["PROP_PUBLIC", "PROP_PRIVATE"]:
                        send_text_message(sender_phone, "Please share your current GPS location using the attachment (📎) button.")

            elif message_type == 'location':
                lat = message_data['location']['latitude']
                lon = message_data['location']['longitude']
                send_text_message(sender_phone, f"✅ Ticket registered successfully! Location: ({lat}, {lon}). Assigned to default worker 'a' (25071a6201).")

        return {"status": "success"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}