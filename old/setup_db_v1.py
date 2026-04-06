import sqlite3

def init_db():
    conn = sqlite3.connect('nsq_audit.db')
    cursor = conn.cursor()

    # 1. Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER,
            title TEXT NOT NULL,
            FOREIGN KEY (trade_id) REFERENCES trades (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER,
            pc_code TEXT NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY (unit_id) REFERENCES units (id)
        )
    ''')

    # 2. Insert ICT Level 3 Trade
    cursor.execute("INSERT INTO trades (name) VALUES (?)", ("ICT Computer Hardware L3",))
    trade_id = cursor.lastrowid

    # 3. Bulk Insert Units and PCs
    nos_content = {
        "Unit 4: Hardware Identification": [
            ("PC 1.1", "Identify internal components (CPU, RAM, Motherboard)"),
            ("PC 2.1", "Use appropriate tools for disassembly"),
            ("PC 3.3", "Identify legacy vs modern expansion slots")
        ],
        "Unit 5: Installation & Integration": [
            ("PC 1.1", "Install CPU and thermal assembly"),
            ("PC 2.2", "Connect storage devices (SATA/NVMe)"),
            ("PC 4.1", "Verify system boot in BIOS/UEFI")
        ],
        "Unit 6: Diagnostic & Troubleshooting": [
            ("PC 1.1", "Identify hardware faults using beep codes"),
            ("PC 3.1", "Reseat components to resolve POST errors"),
            ("PC 5.2", "Update drivers via Device Manager")
        ]
    }

    for unit_title, pcs in nos_content.items():
        cursor.execute("INSERT INTO units (trade_id, title) VALUES (?, ?)", (trade_id, unit_title))
        unit_id = cursor.lastrowid
        for code, desc in pcs:
            cursor.execute("INSERT INTO performance_criteria (unit_id, pc_code, description) VALUES (?, ?, ?)", 
                           (unit_id, code, desc))

    conn.commit()
    conn.close()
    print("Database 'nsq_audit.db' created and populated successfully!")

if __name__ == "__main__":
    init_db()