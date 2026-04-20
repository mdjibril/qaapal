import streamlit as st
from auth_utils import check_auth, login_form
import dashboard, history, admin_nos, admin_users, database as db
import google.generativeai as genai
from groq import Groq
import requests, json
import google.api_core.exceptions
from ai_utils import validate_and_generate

st.set_page_config(page_title="NSQ Portal", layout="wide")

if not check_auth():
    login_form()
else:
    role = st.session_state.get('user_role', 'assessor')
    
    # --- CENTRALIZED SIDEBAR ---
    st.sidebar.title(f"🚀 NSQ Portal v1.0.1")
    st.sidebar.caption(f"Logged in as: {role.capitalize()}")
    
    # 1. AI Settings
    st.sidebar.subheader("📡 AI Provider Settings")
    st.session_state.ai_provider = st.sidebar.selectbox("Provider", ["Gemini", "Groq", "OpenRouter"])
    # ... (Keep your logic here to set st.session_state.target_key and st.session_state.target_model)
    if st.session_state.ai_provider == "Gemini":
        st.session_state.target_key = st.sidebar.text_input("Gemini API Key", type="password")
        # We list simple names; the Router will find the 'models/xxx' version
        st.session_state.target_model = st.sidebar.selectbox("Gemini Preference", ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2-flash", "gemini-2-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-lite"])
    elif st.session_state.ai_provider == "Groq":
        st.session_state.target_key = st.sidebar.text_input("Groq API Key", type="password")
        st.session_state.target_model = st.sidebar.selectbox("Groq Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    elif st.session_state.ai_provider == "OpenRouter":
        st.session_state.target_key = st.sidebar.text_input("OpenRouter Key", type="password")
        st.session_state.target_model = st.sidebar.selectbox("Model", ["anthropic/claude-3-haiku", "nvidia/nemotron-3-super-120b-a12b:free", "arcee-ai/trinity-large-preview:free", "google/gemma-4-31b-it:free"])

    # THE VERIFICATION BUTTON
    if st.session_state.target_key:
        if st.sidebar.button("Verify Connection"):
            with st.sidebar:
                with st.spinner("Checking..."):
                    res = validate_and_generate(st.session_state.ai_provider, st.session_state.target_model, st.session_state.target_key)
                    if "API_ERROR" in str(res):
                        st.error(f"❌ {res}")
                    else:
                        st.success(res) # Shows the "✅ Connected: models/..." message

    dev_mode = st.sidebar.checkbox("🛠️ Dev Mode (Skip AI)", value=False)
    
    env_options = {
        "Morning (Cool)": "The morning air was cool and the lab was quiet, providing a focused atmosphere with plenty of natural light.",
        "Afternoon (Warm)": "The lab temperature was moderate; the ceiling fans were active to maintain a comfortable working environment during the peak afternoon heat.",
        "Technical/Busy": "The lab was active with the hum of server fans and multiple workstations in use, creating a realistic, high-energy technical environment.",
        "Rainy/Overcast": "Due to the weather, the lab was lit with overhead fluorescent lights; the atmosphere was cool and calm.",
        "Custom": "" 
    }
    selected_env_preset = st.sidebar.selectbox("Choose a Preset", list(env_options.keys()))
    st.session_state.default_env_text = env_options[selected_env_preset]

    # 1. Wrap the fetch in a cached function (place this near the top)
    @st.cache_data(ttl=600) # Caches for 10 minutes
    def get_cached_trades():
        return db.fetch_trades()

    # 2. Use the cached version in your sidebar logic
    st.sidebar.markdown("---")
    trades_df = get_cached_trades()

    if not trades_df.empty:
        # We use index to ensure the selector stays on the same item after refresh
        selected_name = st.sidebar.selectbox(
            "Select Trade", 
            trades_df['name'], 
            key="global_trade_select"
        )
        # Update session state
        st.session_state.selected_trade_id = trades_df.loc[
            trades_df['name'] == selected_name, 'id'
        ].iloc[0]

    # 3. Assessor Info
    st.sidebar.markdown("---")
    st.session_state.assessor_name = st.sidebar.text_input("Assessor Name", value="Jibril Dauda Muhammad")
    st.session_state.assessor_id = st.sidebar.text_input("Assessor ID", value="QAA/XXXX/ICT")

    # 4. Navigation
    st.sidebar.markdown("---")
    pages = {"Dashboard": dashboard.main, "📜 My History": history.main}
    if role == 'admin':
        pages["📚 Manage NOS"] = admin_nos.main
        pages["👥 User Management"] = admin_users.main
    
    selection = st.sidebar.radio("Navigation", list(pages.keys()))
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    pages[selection]()
