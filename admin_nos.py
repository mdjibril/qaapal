import streamlit as st
from auth_utils import get_supabase, get_admin_supabase
import pandas as pd

def main():
    st.title("📚 NOS Management (Admin)")

    # 1. Initialization and One-time Loading Logic
    if "admin_nos_cache" not in st.session_state:
        with st.spinner("Loading NOS database..."):
            try:
                # Use admin client to ensure we bypass RLS and see all tables (like trades)
                admin_client = get_admin_supabase()
                st.session_state.admin_nos_cache = {
                    "Trades": admin_client.table("trades").select("*").execute().data,
                    "Units": admin_client.table("units").select("*").execute().data,
                    "Learning Outcomes": admin_client.table("learning_outcomes").select("*").execute().data,
                    "Performance Criteria": admin_client.table("performance_criteria").select("*").execute().data,
                }
            except Exception as e:
                st.error(f"Failed to load NOS data: {e}")
                st.session_state.admin_nos_cache = {"Trades": [], "Units": [], "Learning Outcomes": []}

    tab1, tab2 = st.tabs(["View All Data", "Edit Content"])

    with tab1:
        c1, c2 = st.columns([3, 1])
        with c1:
            table_key = st.selectbox("Select Category", list(st.session_state.admin_nos_cache.keys()))
        with c2:
            st.write("") # Padding
            if st.button("🔄 Refresh Data"):
                del st.session_state.admin_nos_cache
                st.rerun()

        # Display from cached session state (Instant loading)
        data = st.session_state.admin_nos_cache.get(table_key, [])
        display_df = pd.DataFrame(data)

        if not display_df.empty:
            # Search Filter
            search_query = st.text_input(f"🔍 Search in {table_key}", placeholder="Enter code, title, or description...")
            if search_query:
                # Case-insensitive search across all string-converted columns
                mask = display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
                display_df = display_df[mask]
            
        st.dataframe(display_df, use_container_width=True)

    with tab2:
        st.subheader("📝 Edit NOS Content")
        
        edit_type = st.radio("Choose item type to edit:", ["Unit", "Learning Outcome"], horizontal=True)
        
        if edit_type == "Unit":
            units = st.session_state.admin_nos_cache.get("Units", [])
            unit_options = {f"{u['code']}: {u['title']}": u for u in units}
            
            if unit_options:
                selected_label = st.selectbox("Select Unit to Modify", list(unit_options.keys()))
                selected_unit = unit_options[selected_label]
                
                with st.form("edit_unit_form"):
                    new_code = st.text_input("Unit Code", value=selected_unit['code'])
                    new_title = st.text_input("Unit Title", value=selected_unit['title'])
                    
                    if st.form_submit_button("Update Unit"):
                        try:
                            admin_client = get_admin_supabase()
                            admin_client.table("units").update({"code": new_code, "title": new_title}).eq("id", selected_unit['id']).execute()
                            st.success("✅ Unit updated successfully!")
                            del st.session_state.admin_nos_cache # Clear cache to force reload on next access
                            st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")
            else:
                st.info("No units available to edit.")

        elif edit_type == "Learning Outcome":
            los = st.session_state.admin_nos_cache.get("Learning Outcomes", [])
            lo_options = {f"ID {lo['id']} (Unit {lo['unit_id']}): {lo['description'][:60]}...": lo for lo in los}
            
            if lo_options:
                selected_label = st.selectbox("Select LO to Modify", list(lo_options.keys()))
                selected_lo = lo_options[selected_label]
                
                with st.form("edit_lo_form"):
                    new_num = st.text_input("LO Number", value=selected_lo.get('lo_num', ''))
                    new_desc = st.text_area("Description", value=selected_lo['description'])
                    
                    if st.form_submit_button("Update Learning Outcome"):
                        try:
                            admin_client = get_admin_supabase()
                            admin_client.table("learning_outcomes").update({"lo_num": new_num, "description": new_desc}).eq("id", selected_lo['id']).execute()
                            st.success("✅ Learning Outcome updated!")
                            del st.session_state.admin_nos_cache
                            st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")