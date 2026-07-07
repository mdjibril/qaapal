import streamlit as st
import pandas as pd
import database as db

def main():
    st.title("🛡️ Super Admin Dashboard")
    st.markdown("High-level system overview, API status, and audit logs.")
    
    # Check if super admin
    if st.session_state.get('user_role') != 'admin':
        st.error("Unauthorized access.")
        return
    
    tab_overview, tab_qa, tab_api, tab_payments = st.tabs([
        "📊 Overview", "📋 QA & Audit Logs", "📡 API Status", "💳 Payment Logs (Mock)"
    ])
    
    with tab_overview:
        st.subheader("System Metrics")
        metrics = db.fetch_system_metrics()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", metrics.get('total_users', 0))
        col2.metric("Total Organizations", metrics.get('total_orgs', 0))
        col3.metric("Total Reports Generated", metrics.get('total_reports', 0))
        
    with tab_qa:
        st.subheader("Recent Assessment Reports")
        reports = db.fetch_recent_reports(limit=50)
        if reports:
            df = pd.DataFrame(reports)
            if not df.empty:
                # Select important columns for viewing
                view_cols = ['created_at', 'student_name', 'trade_id', 'created_by']
                available_cols = [c for c in view_cols if c in df.columns]
                st.dataframe(df[available_cols] if available_cols else df, width='stretch')
                
                # Allow inspecting a specific report
                st.markdown("---")
                selected_report_id = st.selectbox("Inspect Full Report", df['id'].tolist())
                if selected_report_id:
                    report_data = df[df['id'] == selected_report_id].iloc[0]
                    st.text_area("Report Content", value=report_data.get('report_text', ''), height=300, disabled=True)
        else:
            st.info("No recent reports found.")
            
    with tab_api:
        st.subheader("API Status & Secrets")
        st.write("Current API configuration loaded from `st.secrets`:")
        
        # We don't expose actual keys, just their presence
        import os
        try:
            gemini_present = "INTERNAL_AI_KEY" in st.secrets or "INTERNAL_AI_KEY" in os.environ
            groq_present = "GROQ_API_KEY" in st.secrets or "GROQ_API_KEY" in os.environ
            openrouter_present = "OPENROUTER_API_KEY" in st.secrets or "OPENROUTER_API_KEY" in os.environ
            vertex_present = "vertex_ai" in st.secrets or "VERTEX_AI" in os.environ
        except Exception:
            gemini_present = "INTERNAL_AI_KEY" in os.environ
            groq_present = "GROQ_API_KEY" in os.environ
            openrouter_present = "OPENROUTER_API_KEY" in os.environ
            vertex_present = "VERTEX_AI" in os.environ
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gemini Key", "Configured" if gemini_present else "Missing")
        c2.metric("Groq Key", "Configured" if groq_present else "Missing")
        c3.metric("Openrouter Key", "Configured" if openrouter_present else "Missing")
        c4.metric("Vertex AI", "Configured" if vertex_present else "Missing")
        
        st.info("API Routing fallback strategy is currently managed directly via Streamlit secrets and environment variables.")
        
    with tab_payments:
        st.subheader("Mock Webhook Listener")
        st.write("This interface simulates viewing webhook events from Selar/Monnify.")
        
        mock_logs = [
            {"date": "2026-07-01 10:00", "provider": "Selar", "status": "SUCCESS", "amount": "₦7000", "org_email": "test@org.com"},
            {"date": "2026-07-02 08:30", "provider": "Monnify", "status": "FAILED", "amount": "₦7000", "org_email": "failed@org.com"}
        ]
        st.dataframe(pd.DataFrame(mock_logs), width='stretch')
        st.info("Note: Actual webhook processing runs externally via your email listener updating Supabase functions.")
