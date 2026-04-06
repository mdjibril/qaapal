import streamlit as st
import sqlite3

st.set_page_config(page_title="NSQ Admin Panel", layout="wide")

def get_db_connection():
    return sqlite3.connect('nsq_audit.db')

st.title("⚙️ NSQ Database Manager")
st.info("Use this panel to update the National Occupational Standards (NOS) for different trades.")

# --- TABS FOR MANAGEMENT ---
tab1, tab2, tab3, tab4 = st.tabs(["Trades", "Units", "Learning Outcomes", "Performance Criteria"])

# --- 1. MANAGE TRADES ---
with tab1:
    st.subheader("Manage Trades")
    with st.form("add_trade"):
        new_trade = st.text_input("New Trade Name (e.g., Solar PV Installation L2)")
        if st.form_submit_button("Add Trade"):
            conn = get_db_connection()
            conn.execute("INSERT INTO trades (name) VALUES (?)", (new_trade,))
            conn.commit()
            st.success(f"Added {new_trade}")

# --- 2. MANAGE UNITS ---
with tab2:
    st.subheader("Manage Units")
    conn = get_db_connection()
    trades = conn.execute("SELECT id, name FROM trades").fetchall()
    
    with st.form("add_unit"):
        trade_choice = st.selectbox("Assign to Trade", trades, format_func=lambda x: x[1])
        u_code = st.text_input("Unit Code (e.g., ICT/CMR/007/L3)")
        u_title = st.text_input("Unit Title")
        if st.form_submit_button("Add Unit"):
            conn.execute("INSERT INTO units (trade_id, code, title) VALUES (?, ?, ?)", 
                         (trade_choice[0], u_code, u_title))
            conn.commit()
            st.success("Unit Added!")

# --- 3. MANAGE LEARNING OUTCOMES (LOs) ---
with tab3:
    st.subheader("Manage Learning Outcomes")
    units = conn.execute("SELECT id, code, title FROM units").fetchall()
    
    with st.form("add_lo"):
        unit_choice = st.selectbox("Assign to Unit", units, format_func=lambda x: f"{x[1]}: {x[2]}")
        lo_num = st.text_input("LO Number (e.g., LO 1)")
        lo_desc = st.text_input("LO Description")
        if st.form_submit_button("Add LO"):
            conn.execute("INSERT INTO learning_outcomes (unit_id, lo_num, desc) VALUES (?, ?, ?)", 
                         (unit_choice[0], lo_num, lo_desc))
            conn.commit()
            st.success("LO Added!")

# --- 4. MANAGE PERFORMANCE CRITERIA (PCs) ---
with tab4:
    st.subheader("Manage Performance Criteria")
    # Get LOs and their parent Unit info for clarity
    query = """
        SELECT lo.id, u.code, lo.lo_num, lo.desc 
        FROM learning_outcomes lo 
        JOIN units u ON lo.unit_id = u.id
    """
    los = conn.execute(query).fetchall()
    
    with st.form("add_pc"):
        lo_choice = st.selectbox("Assign to LO", los, format_func=lambda x: f"{x[1]} -> {x[2]}: {x[3]}")
        pc_code = st.text_input("PC Code (e.g., PC 1.1)")
        pc_desc = st.text_area("PC Description")
        if st.form_submit_button("Add PC"):
            conn.execute("INSERT INTO performance_criteria (lo_id, pc_code, desc) VALUES (?, ?, ?)", 
                         (lo_choice[0], pc_code, pc_desc))
            conn.commit()
            st.success("PC Added!")

# --- VIEW CURRENT DATABASE ---
st.markdown("---")
if st.checkbox("Show Raw Database Tables"):
    table_choice = st.selectbox("Select Table to View", ["trades", "units", "learning_outcomes", "performance_criteria"])
    df = conn.execute(f"SELECT * FROM {table_choice}").fetchall()
    st.table(df)

conn.close()