import time

import streamlit as st

from auth_utils import get_supabase
from app_state import ensure_session_defaults


def main():
    ensure_session_defaults(
        {
            "account_settings_status": "",
        }
    )

    st.title("⚙️ Account Settings")
    st.caption("Update your name, phone number, and password from one place.")

    user = st.session_state.get("user_session")
    if not user:
        st.error("No active session found.")
        return

    current_name = st.session_state.get("assessor_full_name", "")
    current_phone = st.session_state.get("assessor_phone", "")
    current_email = getattr(user, "email", "") or st.session_state.get("user_email", "")

    st.markdown("---")
    st.subheader("Profile Details")
    st.caption("These values are used across the app for labels and contact details.")

    with st.form("profile_update_form"):
        full_name = st.text_input("Full Name", value=current_name)
        phone = st.text_input("Phone Number", value=current_phone, placeholder="+234...")
        save_profile = st.form_submit_button("Save Profile")

    if save_profile:
        full_name = full_name.strip()
        phone = phone.strip()

        if not full_name:
            st.error("Full name cannot be empty.")
        elif len(full_name) > 150:
            st.error("Full name is too long.")
        elif phone and len(phone) > 30:
            st.error("Phone number is too long.")
        else:
            try:
                supabase = get_supabase()
                supabase.table("user_profiles").update(
                    {
                        "full_name": full_name,
                        "phone": phone or None,
                    }
                ).eq("id", user.id).execute()

                st.session_state.assessor_full_name = full_name
                st.session_state.assessor_phone = phone
                st.success("Profile updated successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update profile: {e}")

    st.markdown("---")
    st.subheader("Account Email")
    st.info(current_email or "No email found for the current session.")

    st.markdown("---")
    st.subheader("Change Password")
    st.caption("Use this form to update your login password.")

    with st.form("password_update_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        save_password = st.form_submit_button("Update Password")

    if save_password:
        if not new_password or not confirm_password:
            st.error("Please fill in both password fields.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            try:
                supabase = get_supabase()
                supabase.auth.update_user({"password": new_password})
                st.success("Password updated successfully. Please sign in again.")
                time.sleep(1.5)
                st.session_state.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update password: {e}")
