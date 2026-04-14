import streamlit as st
from auth_utils import check_auth, login_form
import dashboard, admin_page # Your other pages

st.set_page_config(page_title="NSQ Portal", layout="wide")

if not check_auth():
    login_form()
else:
    # Sidebar Navigation
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Admin Settings"] if st.session_state.get('user_role') == 'admin' else ["Dashboard"])
    
    if menu == "Dashboard":
        dashboard.main()
    elif menu == "Admin Settings":
        admin_page.main()

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()