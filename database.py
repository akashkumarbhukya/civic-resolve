import sqlite3

def init_db():
    conn = sqlite3.connect('civic_resolve.db')
    cursor = conn.cursor()

    # 1. Create tables if they don't exist at all
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
    conn.commit()

    # 2. THE BULLETPROOF FIX: PRAGMA Schema Migration
    # This actively checks the tables and forces missing columns to be added safely.
    def ensure_column(table, column, datatype):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            print(f"Injecting missing column: {column} into {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
            conn.commit()

    # Update Workforce Table
    ensure_column("workforce", "govt_emp_id", "TEXT")
    ensure_column("workforce", "name", "TEXT")
    ensure_column("workforce", "verification_code", "TEXT")
    ensure_column("workforce", "approved_by", "TEXT")
    ensure_column("workforce", "otp", "TEXT")
    ensure_column("workforce", "otp_expiry", "REAL")

    # Update Tickets Table
    ensure_column("tickets", "material_requested", "TEXT")
    ensure_column("tickets", "material_status", "TEXT")
    ensure_column("tickets", "vendor_phone", "TEXT")

    # 3. Seed Government Employees
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
    print("Database verified securely. Schema is up to date!")

if __name__ == "__main__":
    init_db()