import streamlit as st
import pandas as pd
from auth_utils import get_admin_supabase

def main():
    st.title("💬 Product Feedback")
    st.write("View feedback submitted by users across the application.")
    
    try:
        admin_client = get_admin_supabase()
        
        # Fetch feedback data with user details
        response = admin_client.table("product_feedback")\
            .select("created_at, rating, comment, source_page, assessor_role, user_profiles(email, full_name)")\
            .order("created_at", desc=True)\
            .execute()
        
        if response.data:
            flat_data = []
            for row in response.data:
                profile = row.get('user_profiles') or {}
                flat_data.append({
                    "Date": pd.to_datetime(row.get('created_at')).strftime("%Y-%m-%d %H:%M"),
                    "Rating": "👍 Helpful" if row.get('rating') == 1 else "👎 Needs Improvement",
                    "Comment": row.get('comment') or "",
                    "Page": row.get('source_page', '').replace('_', ' ').title(),
                    "Role": row.get('assessor_role') or "N/A",
                    "User Name": profile.get('full_name') or "Unknown",
                    "User Email": profile.get('email') or "Unknown"
                })
                
            df = pd.DataFrame(flat_data)
            
            # Display Quick Metrics
            m1, m2, m3 = st.columns(3)
            total = len(df)
            positive = len(df[df['Rating'] == "👍 Helpful"])
            negative = len(df[df['Rating'] == "👎 Needs Improvement"])
            
            m1.metric("Total Feedback", total)
            m2.metric("Positive (👍)", positive)
            m3.metric("Negative (👎)", negative)
            
            st.markdown("---")
            
            # Display the feedback list
            st.dataframe(
                df,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Rating": st.column_config.TextColumn("Rating", width="small"),
                    "Comment": st.column_config.TextColumn("Comment", width="large"),
                    "Page": st.column_config.TextColumn("Source Page", width="medium"),
                    "Role": st.column_config.TextColumn("Role", width="small"),
                    "User Name": st.column_config.TextColumn("User Name", width="medium"),
                    "User Email": st.column_config.TextColumn("User Email", width="medium")
                },
                hide_index=True,
                width='stretch'
            )
        else:
            st.info("No feedback has been submitted yet.")
            
        if st.button("Refresh Data"):
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading feedback data: {e}")
