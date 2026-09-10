import sqlite3

def init_db():
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS citizens (
        phone_number TEXT PRIMARY KEY,
        pincode TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workforce (
        worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE,
        worker_type TEXT,
        trade_skill TEXT,
        pincode TEXT,
        status TEXT,
        govt_emp_id TEXT UNIQUE,
        name TEXT,
        verification_code TEXT, 
        approved_by TEXT 
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        citizen_phone TEXT,
        category TEXT,
        property_type TEXT,
        pincode TEXT,
        latitude TEXT,
        longitude TEXT,
        status TEXT,
        assigned_worker_phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Safely migrate existing databases with new columns (ignores if they already exist)
    try:
        cursor.execute("ALTER TABLE tickets ADD COLUMN material_requested TEXT")
        cursor.execute("ALTER TABLE tickets ADD COLUMN material_status TEXT")
        cursor.execute("ALTER TABLE tickets ADD COLUMN vendor_phone TEXT")
    except sqlite3.OperationalError:
        pass 

    try:
        cursor.execute("ALTER TABLE workforce ADD COLUMN otp TEXT")
        cursor.execute("ALTER TABLE workforce ADD COLUMN otp_expiry REAL")
    except sqlite3.OperationalError:
        pass 

    # Seed Government Employees
    govt_employees = [
        ("25071a6201", "a", "9398750534"),
        ("25071a6202", "b", "6309931174"),
        ("25071a6203", "c", "9000171576"),
        ("25071a6204", "d", "9182048099"),
        ("25071a6205", "e", "7702895327"),
        ("25071a6206", "f", "9398750534") 
    ]

    for emp_id, name, phone in govt_employees:
        cursor.execute('''
        INSERT OR IGNORE INTO workforce (phone_number, worker_type, trade_skill, pincode, status, govt_emp_id, name)
        VALUES (?, 'GOVT', 'GENERAL_CIVIC', '506134', 'ACTIVE', ?, ?)
        ''', (phone, emp_id, name))

    conn.commit()
    conn.close()
    print("Database verified securely. OTP & Procurement logic ready.")

if __name__ == "__main__":
    init_db()