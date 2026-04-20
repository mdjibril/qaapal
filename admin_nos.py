import streamlit as st
from auth_utils import get_supabase
import pandas as pd

def main():
    st.title("📚 NOS Management (Admin)")
    supabase = get_supabase()

    tab1, tab2 = st.tabs(["View All Data", "Edit Content"])

    with tab1:
        table = st.selectbox("Select Table to View", ["trades", "units", "learning_outcomes"])
        data = supabase.table(table).select("*").execute()
        st.dataframe(pd.DataFrame(data.data))

    with tab2:
        st.warning("Editing logic for Supabase should be handled carefully via the ID.")
        # Re-insert your update/delete logic here using:
        # supabase.table("units").update({"title": new_title}).eq("id", u_id).execute()