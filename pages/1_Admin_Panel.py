# import streamlit as st
# import sqlite3

# st.set_page_config(page_title="NSQ Admin Panel", layout="wide")

# def get_db_connection():
#     return sqlite3.connect('nsq_audit.db')

# st.title("⚙️ NSQ Database Manager")

# # Ensure the History table exists
# conn = get_db_connection()
# conn.execute("""
#     CREATE TABLE IF NOT EXISTS assessment_reports (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         student_name TEXT,
#         trade_id INTEGER,
#         unit_codes TEXT,
#         report_text TEXT,
#         assessment_date TEXT,
#         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#     )
# """)
# conn.commit()

# tab1, tab2, tab3, tab4 = st.tabs(["Trades", "Units", "Learning Outcomes", "Performance Criteria"])

# # --- 1. MANAGE TRADES ---
# with tab1:
#     st.subheader("Manage Trades")
#     trades = conn.execute("SELECT id, name FROM trades").fetchall()
#     if trades:
#         trade_to_manage = st.selectbox("Select Trade", trades, format_func=lambda x: x[1], key="t_select")
#         col1, col2 = st.columns(2)
#         with col1:
#             updated_t_name = st.text_input("Update Name", value=trade_to_manage[1])
#             if st.button("Update Trade"):
#                 conn.execute("UPDATE trades SET name = ? WHERE id = ?", (updated_t_name, trade_to_manage[0]))
#                 conn.commit()
#                 st.rerun()
#         with col2:
#             confirm_t = st.checkbox("Confirm Deletion", key="del_t_conf")
#             if st.button("Delete Trade", type="primary", disabled=not confirm_t):
#                 conn.execute("DELETE FROM trades WHERE id = ?", (trade_to_manage[0],))
#                 conn.commit()
#                 st.rerun()
#     else:
#         st.info("No trades found.")

# # --- 2. MANAGE UNITS (FIXED INDEX ERROR) ---
# with tab2:
#     st.subheader("Manage Units")
#     # We MUST select all 4 columns: id(0), trade_id(1), code(2), title(3)
#     units = conn.execute("SELECT id, trade_id, code, title FROM units").fetchall()
    
#     if units:
#         unit_to_manage = st.selectbox(
#             "Select Unit", 
#             units, 
#             format_func=lambda x: f"{x[2] if len(x) > 2 else 'N/A'}: {x[3] if len(x) > 3 else 'No Title'}", 
#             key="u_select"
#         )
#         u_col1, u_col2 = st.columns(2)
#         with u_col1:
#             new_code = st.text_input("Edit Code", value=unit_to_manage[2])
#             new_title = st.text_input("Edit Title", value=unit_to_manage[3])
#             if st.button("Update Unit"):
#                 conn.execute("UPDATE units SET code = ?, title = ? WHERE id = ?", (new_code, new_title, unit_to_manage[0]))
#                 conn.commit()
#                 st.rerun()
#         with u_col2:
#             confirm_u = st.checkbox("Confirm Deletion", key="del_u_conf")
#             if st.button("Delete Unit", type="primary", disabled=not confirm_u):
#                 conn.execute("DELETE FROM units WHERE id = ?", (unit_to_manage[0],))
#                 conn.commit()
#                 st.rerun()
#     else:
#         st.info("No units found.")

# # --- 3. MANAGE LOs ---
# with tab3:
#     st.subheader("Manage Learning Outcomes")
#     los = conn.execute("SELECT id, lo_num, desc FROM learning_outcomes").fetchall()
#     if los:
#         lo_to_manage = st.selectbox("Select LO", los, format_func=lambda x: f"{x[1]}: {x[2]}", key="lo_select")
#         l_col1, l_col2 = st.columns(2)
#         with l_col1:
#             upd_lo_num = st.text_input("LO Number", value=lo_to_manage[1])
#             upd_lo_desc = st.text_area("LO Description", value=lo_to_manage[2])
#             if st.button("Update LO"):
#                 conn.execute("UPDATE learning_outcomes SET lo_num = ?, desc = ? WHERE id = ?", (upd_lo_num, upd_lo_desc, lo_to_manage[0]))
#                 conn.commit()
#                 st.rerun()
#         with l_col2:
#             confirm_lo = st.checkbox("Confirm Deletion", key="del_lo_conf")
#             if st.button("Delete LO", type="primary", disabled=not confirm_lo):
#                 conn.execute("DELETE FROM learning_outcomes WHERE id = ?", (lo_to_manage[0],))
#                 conn.commit()
#                 st.rerun()
#     else:
#         st.info("No Learning Outcomes found.")

# # --- 4. MANAGE PCs ---
# with tab4:
#     st.subheader("Manage Performance Criteria")
#     pcs = conn.execute("SELECT id, pc_code, desc FROM performance_criteria").fetchall()
#     if pcs:
#         pc_to_manage = st.selectbox("Select PC", pcs, format_func=lambda x: f"{x[1]}: {x[2]}", key="pc_select")
#         p_col1, p_col2 = st.columns(2)
#         with p_col1:
#             upd_pc_code = st.text_input("PC Code", value=pc_to_manage[1])
#             upd_pc_desc = st.text_area("PC Description", value=pc_to_manage[2])
#             if st.button("Update PC"):
#                 conn.execute("UPDATE performance_criteria SET pc_code = ?, desc = ? WHERE id = ?", (upd_pc_code, upd_pc_desc, pc_to_manage[0]))
#                 conn.commit()
#                 st.rerun()
#         with p_col2:
#             confirm_pc = st.checkbox("Confirm Deletion", key="del_pc_conf")
#             if st.button("Delete PC", type="primary", disabled=not confirm_pc):
#                 conn.execute("DELETE FROM performance_criteria WHERE id = ?", (pc_to_manage[0],))
#                 conn.commit()
#                 st.rerun()
#     else:
#         st.info("No Performance Criteria found.")

# # --- VIEW CURRENT DATABASE ---
# st.markdown("---")
# if st.checkbox("Show Raw Database Tables"):
#     table_choice = st.selectbox("Select Table to View", ["trades", "units", "learning_outcomes", "performance_criteria"])
#     df = conn.execute(f"SELECT * FROM {table_choice}").fetchall()
#     st.table(df)

# conn.close()
# ---------------------------------------OLD
# import streamlit as st
# import sqlite3

# st.set_page_config(page_title="NSQ Admin Panel", layout="wide")

# def get_db_connection():
#     conn = sqlite3.connect('nsq_audit.db')
#     # Force foreign key support even if not using cascade
#     conn.execute("PRAGMA foreign_keys = ON")
#     return conn

# st.title("⚙️ NSQ Database Manager")

# conn = get_db_connection()

# # --- 1. MANAGE TRADES (With Deep Clean) ---
# tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trades", "Units", "Learning Outcomes", "Performance Criteria", "Database Tools"])

# with tab1:
#     st.subheader("Manage Trades")
#     trades = conn.execute("SELECT id, name FROM trades").fetchall()
#     if trades:
#         trade_to_manage = st.selectbox("Select Trade", trades, format_func=lambda x: x[1], key="t_select")
#         col1, col2 = st.columns(2)
#         with col1:
#             updated_t_name = st.text_input("Update Name", value=trade_to_manage[1])
#             if st.button("Update Trade"):
#                 conn.execute("UPDATE trades SET name = ? WHERE id = ?", (updated_t_name, trade_to_manage[0]))
#                 conn.commit()
#                 st.success("Trade name updated!")
#                 st.rerun()
#         with col2:
#             st.warning("🗑️ Deleting a Trade will remove all associated Units, LOs, and PCs.")
#             confirm_t = st.checkbox("Confirm Deep Delete", key="del_t_conf")
#             if st.button("Delete Trade Node", type="primary", disabled=not confirm_t):
#                 t_id = trade_to_manage[0]
#                 # Manual Cascade: Delete from bottom up
#                 conn.execute("DELETE FROM performance_criteria WHERE lo_id IN (SELECT id FROM learning_outcomes WHERE unit_id IN (SELECT id FROM units WHERE trade_id = ?))", (t_id,))
#                 conn.execute("DELETE FROM learning_outcomes WHERE unit_id IN (SELECT id FROM units WHERE trade_id = ?)", (t_id,))
#                 conn.execute("DELETE FROM units WHERE trade_id = ?", (t_id,))
#                 conn.execute("DELETE FROM trades WHERE id = ?", (t_id,))
#                 conn.commit()
#                 st.success("Entire Trade Node deleted.")
#                 st.rerun()
#     else:
#         st.info("No trades found.")



# # --- 5. DATABASE TOOLS (MAINTENANCE) ---
# with tab5:
#     st.subheader("🗑️ Global History Maintenance")
#     count = conn.execute("SELECT COUNT(*) FROM assessment_reports").fetchone()[0]
#     st.write(f"Total reports in history: **{count}**")
    
#     col_m1, col_m2 = st.columns(2)
#     with col_m1:
#         st.info("Remove the oldest 15 reports to free space.")
#         if st.button("Delete Oldest 15"):
#             conn.execute("DELETE FROM assessment_reports WHERE id IN (SELECT id FROM assessment_reports ORDER BY id ASC LIMIT 15)")
#             conn.commit()
#             st.success("Deleted 15 oldest records.")
#             st.rerun()
            
#     with col_m2:
#         st.error("DANGER: This wipes the entire assessment history.")
#         conf_wipe = st.checkbox("Confirm TOTAL WIPE")
#         if st.button("Wipe All History", type="primary", disabled=not conf_wipe):
#             conn.execute("DELETE FROM assessment_reports")
#             conn.execute("DELETE FROM sqlite_sequence WHERE name='assessment_reports'")
#             conn.commit()
#             st.rerun()

# conn.close()

import streamlit as st
import sqlite3

st.set_page_config(page_title="NSQ Admin Panel", layout="wide")

def get_db_connection():
    conn = sqlite3.connect('nsq_audit.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

st.title("⚙️ NSQ Database Manager")
conn = get_db_connection()

# --- SUCCESS MESSAGE LOGIC ---
if 'delete_success' in st.session_state:
    st.success(st.session_state.delete_success)
    del st.session_state.delete_success

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trades", "Units", "LOs", "PCs", "Database Tools"])

# --- 1. MANAGE TRADES ---
with tab1:
    st.subheader("Manage Trades")
    trades = conn.execute("SELECT id, name FROM trades").fetchall()
    if trades:
        trade_to_manage = st.selectbox("Select Trade", trades, format_func=lambda x: x[1], key="t_select")
        col1, col2 = st.columns(2)
        with col1:
            updated_t_name = st.text_input("Update Name", value=trade_to_manage[1])
            if st.button("Update Trade"):
                conn.execute("UPDATE trades SET name = ? WHERE id = ?", (updated_t_name, trade_to_manage[0]))
                conn.commit()
                st.rerun()
        with col2:
            st.warning("🗑️ This will remove the Trade and all its associated children.")
            confirm_t = st.checkbox("Confirm Deep Delete", key="del_t_conf", value=False)
            
            if st.button("Delete Trade Node", type="primary", disabled=not confirm_t):
                t_id = trade_to_manage[0]
                t_name = trade_to_manage[1]
                # Deep Clean
                conn.execute("DELETE FROM performance_criteria WHERE lo_id IN (SELECT id FROM learning_outcomes WHERE unit_id IN (SELECT id FROM units WHERE trade_id = ?))", (t_id,))
                conn.execute("DELETE FROM learning_outcomes WHERE unit_id IN (SELECT id FROM units WHERE trade_id = ?)", (t_id,))
                conn.execute("DELETE FROM units WHERE trade_id = ?", (t_id,))
                conn.execute("DELETE FROM trades WHERE id = ?", (t_id,))
                conn.commit()
                
                # Success Handling: Set session state to show message after rerun
                st.session_state.delete_success = f"Successfully deleted Node: {t_name}"
                st.rerun()
    else:
        st.info("No trades found.")

# --- 2. MANAGE UNITS (With Deep Clean) ---
with tab2:
    st.subheader("Manage Units")
    units = conn.execute("SELECT id, trade_id, code, title FROM units").fetchall()
    if units:
        unit_to_manage = st.selectbox(
            "Select Unit", 
            units, 
            format_func=lambda x: f"{x[2]}: {x[3]}", 
            key="u_select"
        )
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            new_code = st.text_input("Edit Code", value=unit_to_manage[2])
            new_title = st.text_input("Edit Title", value=unit_to_manage[3])
            if st.button("Update Unit"):
                conn.execute("UPDATE units SET code = ?, title = ? WHERE id = ?", (new_code, new_title, unit_to_manage[0]))
                conn.commit()
                st.rerun()
        with u_col2:
            st.warning("Deleting a Unit removes all its LOs and PCs.")
            confirm_u = st.checkbox("Confirm Unit Delete", key="del_u_conf")
            if st.button("Delete Unit Node", type="primary", disabled=not confirm_u):
                u_id = unit_to_manage[0]
                conn.execute("DELETE FROM performance_criteria WHERE lo_id IN (SELECT id FROM learning_outcomes WHERE unit_id = ?)", (u_id,))
                conn.execute("DELETE FROM learning_outcomes WHERE unit_id = ?", (u_id,))
                conn.execute("DELETE FROM units WHERE id = ?", (u_id,))
                conn.commit()
                st.rerun()
    else:
        st.info("No units found.")

# --- 3. MANAGE LOs (With Deep Clean) ---
with tab3:
    st.subheader("Manage Learning Outcomes")
    los = conn.execute("SELECT id, lo_num, desc FROM learning_outcomes").fetchall()
    if los:
        lo_to_manage = st.selectbox("Select LO", los, format_func=lambda x: f"{x[1]}: {x[2]}", key="lo_select")
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            upd_lo_num = st.text_input("LO Number", value=lo_to_manage[1])
            upd_lo_desc = st.text_area("LO Description", value=lo_to_manage[2])
            if st.button("Update LO"):
                conn.execute("UPDATE learning_outcomes SET lo_num = ?, desc = ? WHERE id = ?", (upd_lo_num, upd_lo_desc, lo_to_manage[0]))
                conn.commit()
                st.rerun()
        with l_col2:
            st.warning("Deleting an LO removes all its PCs.")
            confirm_lo = st.checkbox("Confirm LO Delete", key="del_lo_conf")
            if st.button("Delete LO Node", type="primary", disabled=not confirm_lo):
                lo_id = lo_to_manage[0]
                conn.execute("DELETE FROM performance_criteria WHERE lo_id = ?", (lo_id,))
                conn.execute("DELETE FROM learning_outcomes WHERE id = ?", (lo_id,))
                conn.commit()
                st.rerun()

# --- 4. MANAGE PCs ---
with tab4:
    st.subheader("Manage Performance Criteria")
    pcs = conn.execute("SELECT id, pc_code, desc FROM performance_criteria").fetchall()
    if pcs:
        pc_to_manage = st.selectbox("Select PC", pcs, format_func=lambda x: f"{x[1]}: {x[2]}", key="pc_select")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            upd_pc_code = st.text_input("PC Code", value=pc_to_manage[1])
            upd_pc_desc = st.text_area("PC Description", value=pc_to_manage[2])
            if st.button("Update PC"):
                conn.execute("UPDATE performance_criteria SET pc_code = ?, desc = ? WHERE id = ?", (upd_pc_code, upd_pc_desc, pc_to_manage[0]))
                conn.commit()
                st.rerun()
        with p_col2:
            confirm_pc = st.checkbox("Confirm PC Delete", key="del_pc_conf")
            if st.button("Delete PC", type="primary", disabled=not confirm_pc):
                conn.execute("DELETE FROM performance_criteria WHERE id = ?", (pc_to_manage[0],))
                conn.commit()
                st.rerun()

# --- 5. DATABASE TOOLS (ARCHIVE LOGIC) ---
with tab5:
    st.subheader("📦 History Archiving")
    count = conn.execute("SELECT COUNT(*) FROM assessment_reports").fetchone()[0]
    arch_count = conn.execute("SELECT COUNT(*) FROM archived_reports").fetchone()[0]
    
    st.write(f"Active Reports: **{count}** | Archived Reports: **{arch_count}**")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.info("Move the oldest 15 reports to the Archive.")
        if st.button("Archive Oldest 15"):
            if count > 0:
                # 1. Copy to Archive
                conn.execute("""
                    INSERT INTO archived_reports 
                    SELECT * FROM assessment_reports ORDER BY id ASC LIMIT 15
                """)
                # 2. Delete from Active
                conn.execute("""
                    DELETE FROM assessment_reports 
                    WHERE id IN (SELECT id FROM assessment_reports ORDER BY id ASC LIMIT 15)
                """)
                conn.commit()
                st.session_state.delete_success = "15 records moved to Archive."
                st.rerun()
            
    with col_m2:
        st.error("Archive All: Moves entire history to Archive.")
        conf_wipe = st.checkbox("Confirm ARCHIVE ALL", key="wipe_arch")
        if st.button("Move All to Archive", type="primary", disabled=not conf_wipe):
            conn.execute("INSERT INTO archived_reports SELECT * FROM assessment_reports")
            conn.execute("DELETE FROM assessment_reports")
            conn.execute("DELETE FROM sqlite_sequence WHERE name='assessment_reports'")
            conn.commit()
            st.session_state.delete_success = "All records safely archived."
            st.rerun()

# --- VIEW RAW DATABASE (NO PYARROW VERSION) ---
st.markdown("---")
if st.checkbox("🔍 Show Raw Database Tables"):
    table_choice = st.selectbox(
        "Select Table", 
        ["trades", "units", "learning_outcomes", "performance_criteria", "assessment_reports", "archived_reports"]
    )
    
    # Fetch data and column names
    cursor = conn.execute(f"SELECT * FROM {table_choice} LIMIT 50")
    raw_data = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    
    if raw_data:
        # Build a Markdown table manually to bypass st.dataframe/pyarrow
        header = "| " + " | ".join(cols) + " |"
        separator = "| " + " | ".join(["---"] * len(cols)) + " |"
        
        rows = []
        for row in raw_data:
            # Clean data to ensure it doesn't break markdown (remove newlines)
            clean_row = [str(item).replace("\n", " ").replace("|", "\\|") for item in row]
            rows.append("| " + " | ".join(clean_row) + " |")
        
        markdown_table = f"{header}\n{separator}\n" + "\n".join(rows)
        
        st.markdown(f"### Table: {table_choice}")
        st.markdown(markdown_table)
    else:
        st.info(f"The table '{table_choice}' is currently empty.")

conn.close()