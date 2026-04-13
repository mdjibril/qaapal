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

    conn.execute("""
    CREATE TABLE IF NOT EXISTS archived_reports (
        id INTEGER PRIMARY KEY,
        student_name TEXT,
        trade_id INTEGER,
        unit_codes TEXT,
        report_text TEXT,
        assessment_date TEXT,
        timestamp DATETIME
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()