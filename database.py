import sqlite3

def init_db():
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()

    # Table 1: Citizens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS citizens (
        phone_number TEXT PRIMARY KEY,
        pincode TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table 2: The Workforce (Govt & Private)
    # This matches the Railway model. Govt workers can be bulk uploaded.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workforce (
        worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE,
        worker_type TEXT, -- 'GOVT', 'PRIVATE_TECH', 'VENDOR'
        trade_skill TEXT,
        pincode TEXT,
        status TEXT, -- 'ACTIVE', 'PENDING_APPROVAL', 'INACTIVE'
        govt_emp_id TEXT, -- Null for private workers
        verification_code TEXT, -- The 6-digit code for private workers
        approved_by TEXT -- Tracks which Govt worker approved them
    )
    ''')

    # Table 3: Tickets
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        citizen_phone TEXT,
        category TEXT,
        property_type TEXT, -- 'PUBLIC' or 'PRIVATE'
        pincode TEXT,
        latitude TEXT,
        longitude TEXT,
        status TEXT, -- 'OPEN', 'ASSIGNED', 'RESOLVED', 'ESCALATED'
        assigned_worker_phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()