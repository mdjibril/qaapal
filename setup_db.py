import sqlite3

def init_db():
    conn = sqlite3.connect('nsq_audit.db')
    cursor = conn.cursor()

    # --- 1. Create Tables with LO Hierarchy ---
    cursor.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS units (id INTEGER PRIMARY KEY, trade_id INTEGER, code TEXT, title TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS learning_outcomes (id INTEGER PRIMARY KEY, unit_id INTEGER, lo_num TEXT, desc TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS performance_criteria (id INTEGER PRIMARY KEY, lo_id INTEGER, pc_code TEXT, desc TEXT)")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessment_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        trade_id INTEGER,
        unit_codes TEXT,
        report_text TEXT,
        assessment_date TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

    # --- 2. Insert Trade ---
    cursor.execute("INSERT OR IGNORE INTO trades (id, name) VALUES (1, 'ICT Computer Hardware Repairs L3')")
    
    # --- 3. Data Population (Example for Units 4 & 5) ---
    # Unit 4: Hardware Identification
    cursor.execute("INSERT OR IGNORE INTO units (id, trade_id, code, title) VALUES (4, 1, 'ICT/CMR/004/L3', 'Hardware Identification & Audit')")
    
    # Unit 4 - LO 1
    cursor.execute("INSERT OR IGNORE INTO learning_outcomes (id, unit_id, lo_num, desc) VALUES (1, 4, 'LO 1', 'Identify internal components')")
    cursor.execute("INSERT OR IGNORE INTO performance_criteria (lo_id, pc_code, desc) VALUES (1, 'PC 1.1', 'Identify CPU, RAM, and Motherboard types')")
    cursor.execute("INSERT OR IGNORE INTO performance_criteria (lo_id, pc_code, desc) VALUES (1, 'PC 1.2', 'Identify storage interfaces (SATA, NVMe)')")

    # Unit 5: Installation & Integration
    cursor.execute("INSERT OR IGNORE INTO units (id, trade_id, code, title) VALUES (5, 1, 'ICT/CMR/005/L3', 'Hardware Installation & Integration')")
    
    # Unit 5 - LO 1
    cursor.execute("INSERT OR IGNORE INTO learning_outcomes (id, unit_id, lo_num, desc) VALUES (2, 5, 'LO 1', 'Install Processor and Cooling')")
    cursor.execute("INSERT OR IGNORE INTO performance_criteria (lo_id, pc_code, desc) VALUES (2, 'PC 1.1', 'Apply thermal paste and seat CPU')")
    cursor.execute("INSERT OR IGNORE INTO performance_criteria (lo_id, pc_code, desc) VALUES (2, 'PC 1.2', 'Secure heatsink and connect fan power')")

    conn.commit()
    conn.close()
    print("Database Updated with LO Hierarchy!")

if __name__ == "__main__":
    init_db()