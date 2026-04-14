import streamlit as st
from sqlalchemy import create_engine, text

# Initialize connection using Streamlit's connection pool
def get_engine():
    # For local development, it falls back to sqlite. 
    # For production, define [connections.postgres] in .streamlit/secrets.toml
    try:
        return st.connection("postgres", type="sql")
    except:
        return st.connection("local_db", type="sql", url="sqlite:///nsq_audit.db")

conn = get_engine()

def fetch_trades():
    return conn.query("SELECT id, name FROM trades")

def fetch_nested_nos(trade_id):
    units = conn.query("SELECT id, code, title FROM units WHERE trade_id = :tid", params={"tid": trade_id})
    nested_data = {}
    for _, unit in units.iterrows():
        nested_data[f"{unit['code']}: {unit['title']}"] = fetch_los_and_pcs(unit['id'])
    return nested_data

def fetch_los_and_pcs(unit_id):
    los = conn.query("SELECT id, lo_num, desc FROM learning_outcomes WHERE unit_id = :uid", params={"uid": unit_id})
    lo_structure = {}
    for _, lo in los.iterrows():
        pcs = conn.query("SELECT pc_code, desc FROM performance_criteria WHERE lo_id = :lid", params={"lid": lo['id']})
        lo_structure[f"{lo['lo_num']}: {lo['desc']}"] = [f"{r['pc_code']}: {r['desc']}" for _, r in pcs.iterrows()]
    return lo_structure

def insert_report(name, trade_id, unit_codes, text, date):
    with conn.session as session:
        session.execute(
            text("INSERT INTO assessment_reports (student_name, trade_id, unit_codes, report_text, assessment_date) VALUES (:n, :t, :u, :r, :d)"),
            {"n": name, "t": trade_id, "u": unit_codes, "r": text, "d": str(date)}
        )
        session.commit()