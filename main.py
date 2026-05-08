import streamlit as st
from auth_utils import check_auth, login_form
import dashboard, history, admin_nos, admin_users, personal_statement, database as db
import google.generativeai as genai
from groq import Groq
import requests, json
import google.api_core.exceptions
from ai_utils import validate_and_generate

st.set_page_config(page_title="NSQ Portal", layout="wide")

# Callback function for API key inputs
def update_api_key_session(key_name):
    """Callback to update st.session_state.target_key when an API key input changes."""
    st.session_state.target_key = st.session_state[key_name]

# Define cached functions at the top level to avoid re-definition issues
@st.cache_data(ttl=600)
def get_cached_trades():
    return db.fetch_trades()

if not check_auth():
    login_form()
else:
    role = st.session_state.get('user_role', 'assessor')
    
    # --- CENTRALIZED SIDEBAR ---
    st.sidebar.title(f"🚀 NSQ Portal v1.0.3")
    st.sidebar.caption(f"Logged in as: {role.capitalize()}")
    st.session_state.assessor_name = st.session_state.get('assessor_full_name', 'Jibril Dauda Muhammad')
    st.session_state.assessor_id = st.session_state.get('assessor_id', 'QAA/XXXX/ICT')
    st.sidebar.caption(f"👤 Assessor: {st.session_state.assessor_name}")
    st.sidebar.caption(f"🆔 ID: {st.session_state.assessor_id}")
    
    # Trade Selection Logic
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
    else:
        st.sidebar.error("⚠️ No trades found. Check Supabase connection or table data.")

    env_options = {
        "Morning (Cool)": "The morning air was cool and the lab was quiet, providing a focused atmosphere with plenty of natural light.",
        "Afternoon (Warm)": "The lab temperature was moderate; the ceiling fans were active to maintain a comfortable working environment during the peak afternoon heat.",
        "Technical/Busy": "The lab was active with the hum of server fans and multiple workstations in use, creating a realistic, high-energy technical environment.",
        "Rainy/Overcast": "Due to the weather, the lab was lit with overhead fluorescent lights; the atmosphere was cool and calm.",
        "Custom": "" 
    }
    selected_env_preset = st.sidebar.selectbox("Choose a Preset", list(env_options.keys()))
    st.session_state.default_env_text = env_options[selected_env_preset]

    # 1. AI Settings
    st.sidebar.subheader("📡 AI Provider Settings")
    st.session_state.ai_provider = st.sidebar.selectbox("Provider", ["Gemini", "Groq", "OpenRouter"])
    # ... (Keep your logic here to set st.session_state.target_key and st.session_state.target_model)

    # Initialize target_key to empty string if not already set, or if provider changes
    if 'target_key' not in st.session_state or st.session_state.get('last_provider') != st.session_state.ai_provider:
        st.session_state.target_key = ""
        st.session_state.last_provider = st.session_state.ai_provider

    if st.session_state.ai_provider == "Gemini":
        st.sidebar.text_input("Gemini API Key", type="password", key="gemini_api_key_input", on_change=update_api_key_session, args=("gemini_api_key_input",))
        # Ensure target_key is set even if no change event fired yet (e.g., initial load)
        if st.session_state.target_key == "" and "gemini_api_key_input" in st.session_state:
            st.session_state.target_key = st.session_state.gemini_api_key_input
        # We list simple names; the Router will find the 'models/xxx' version
        st.session_state.target_model = st.sidebar.selectbox("Gemini Preference", ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2-flash", "gemini-2-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-lite"])
    elif st.session_state.ai_provider == "Groq":
        st.sidebar.text_input("Groq API Key", type="password", key="groq_api_key_input", on_change=update_api_key_session, args=("groq_api_key_input",))
        if st.session_state.target_key == "" and "groq_api_key_input" in st.session_state:
            st.session_state.target_key = st.session_state.groq_api_key_input
        st.session_state.target_model = st.sidebar.selectbox("Groq Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    elif st.session_state.ai_provider == "OpenRouter":
        st.sidebar.text_input("OpenRouter Key", type="password", key="openrouter_api_key_input", on_change=update_api_key_session, args=("openrouter_api_key_input",))
        if st.session_state.target_key == "" and "openrouter_api_key_input" in st.session_state:
            st.session_state.target_key = st.session_state.openrouter_api_key_input
        st.session_state.target_model = st.sidebar.selectbox("Model", ["z-ai/glm-4.5-air:free", "openai/gpt-oss-120b:free", "poolside/laguna-m.1:free", "liquid/lfm-2.5-1.2b-thinking:free", "nvidia/nemotron-3-super-120b-a12b:free"])

    # THE VERIFICATION BUTTON
    # The target_key is now updated via the on_change callback, so this condition will be more responsive.
    if st.session_state.get('target_key'):
        if st.sidebar.button("Verify Connection"):
            with st.sidebar:
                with st.spinner("Checking..."):
                    res = validate_and_generate(st.session_state.ai_provider, st.session_state.target_model, st.session_state.target_key)
                    if "API_ERROR" in str(res):
                        st.error(f"❌ {res}")
                    elif "✅ Connected" in str(res):
                        st.success(res) # Shows the "✅ Connected: models/..." message
                    else:
                        st.error(f"Verification failed: {res}")

    if role == 'admin':
        st.sidebar.checkbox("🛠️ Dev Mode (Skip AI)", key="dev_mode")
    
    
    # 4. Navigation
    st.sidebar.markdown("---")
    
    if role == 'student':
        pages = {"✍️ Student Statement": personal_statement.main}
    else:
        pages = {
            "Dashboard": dashboard.main, 
            "✍️ Student Statement": personal_statement.main,
            "📜 My History": history.main
        }
        if role == 'admin':
            pages["📚 Manage NOS"] = admin_nos.main
            pages["👥 User Management"] = admin_users.main
    
    selection = st.sidebar.radio("Navigation", list(pages.keys()))
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    pages[selection]()
