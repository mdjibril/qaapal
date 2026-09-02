import streamlit as st
import datetime
import database as db
from ai_utils import validate_and_generate
from auth_utils import get_secret
from file_utils import export_personal_statement_to_word
from security_utils import sanitize_text_input, sanitize_notes_input
import components
from prompt_builders import build_personal_statement_prompt

# Criteria selection is now handled by components.render_nos_selection

def main():
    st.title("✍️ Personal Statement of Competence")
    st.info("This tool helps students generate a professional narrative of their achievements based on NSQ standards.")

    # 1. Context Selection
    trade_id = st.session_state.get('selected_trade_id')
    trade_level_id = st.session_state.get('selected_trade_level_id')
    if not trade_id:
        st.warning("Please select a trade in the sidebar to begin.")
        return

    # Access shared session info
    provider = st.session_state.get('ai_provider')
    keys = st.session_state.get('target_keys', []) # Now expects a list of keys
    target_model = st.session_state.get('target_model')

    # 2. Input Section
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            raw_student_name = st.text_input("Student Full Name", placeholder="e.g. John Doe")
            student_name = sanitize_text_input(raw_student_name, 100)
        with col2:
            statement_date = st.date_input("Statement Date", datetime.date.today())

    st.markdown("---")
    st.subheader("Step 1: What did you achieve?")
    
    # Fetch NOS data for selection
    nos_data = db.fetch_nested_nos(trade_level_id=trade_level_id, trade_id=trade_id)
    if nos_data:
        components.render_nos_selection(
            nos_data=nos_data,
            prefix="stmt_",
            persistent_set_key="persistent_student_selected_pcs",
            result_list_key="student_selected_pcs",
            select_key_prefix="stmt"
        )
    else:
        st.error("No competency data found for the selected trade.")

    st.markdown("---")
    st.subheader("Step 2: Your Reflection")
    with st.container(border=True):
        raw_reflection = st.text_area(
            "Describe what you did in your own words:",
            placeholder="e.g. I worked on a Dell Optiplex. I had to replace the RAM because the computer was beeping. I used a screwdriver and wore my wrist strap...",
            height=200
        )
    reflection = sanitize_notes_input(raw_reflection, 2000)

    selected_pcs = st.session_state.get('student_selected_pcs', [])
    st.info(f"Selected: {len(selected_pcs)} Performance Criteria")

    st.markdown("---")
    st.subheader("Step 3: Generate Statement")
    
    # Paywall Check
    role = st.session_state.get('user_role')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    using_byok = st.session_state.get('using_byok', False)

    if role == 'admin':
        is_out_of_credits = False
    elif tier == 'free':
        is_out_of_credits = credits <= 0
    else:
        policy = st.session_state.get('_ai_policy', {})
        quota = policy.get('platform_quota')
        if using_byok:
            is_out_of_credits = False
        elif quota == 0:
            is_out_of_credits = True
        elif quota is None:
            is_out_of_credits = False
        else:
            used = st.session_state.get('ai_quota_used', 0) or 0
            is_out_of_credits = used >= quota

    if is_out_of_credits:
        platform_quota = st.session_state.get('_ai_policy', {}).get('platform_quota')
        if tier != 'free' and platform_quota == 0:
            st.warning("🔑 Your plan requires your own AI key. Add a key in the sidebar to generate statements.")
        else:
            selar_base = get_secret(["payments", "selar_link"], "payments__selar_link") or "https://selar.com/nsqassessment-platformpass"
            selar_lifetime_base = get_secret(["payments", "selar_lifetime_link"], "payments__selar_lifetime_link") or "https://selar.com/nsqassessment-lifetime"
            user_email = st.session_state.user_session.email
            upgrade_link = f"{selar_base}?email={user_email}"
            lifetime_upgrade_link = f"{selar_lifetime_base}?email={user_email}"
            st.warning("⚠️ You have 0 credits remaining. Upgrade to continue generating statements.")
            col_up1, col_up2 = st.columns(2)
            with col_up1:
                st.link_button("🚀 Upgrade to Platform Pass", upgrade_link, width='stretch')
            with col_up2:
                st.link_button("💎 Get Lifetime Tier", lifetime_upgrade_link, width='stretch')

    if st.button("Generate My Statement", type="primary", disabled=is_out_of_credits):
        if not reflection:
            st.error("Please provide some reflection notes first.")
        elif not selected_pcs:
            st.error("Please select at least one PC that you achieved.")
        elif not keys: # Check if keys list is empty
            if tier == 'free':
                st.error("⛔ Internal AI key missing. Contact administrator.")
            else:
                st.warning("Please enter your AI API key in the sidebar.")
        else:
            st.session_state.pop("fb_submitted_personal_statement", None)
            with st.status("Crafting Personal Statement...", expanded=True) as status:
                st.write("🧵 Weaving reflection notes with competency standards...")
                trade_context = st.session_state.get("selected_trade_level_name") or st.session_state.get("selected_trade_name") or 'the specific trade'
                prompt_bundle = build_personal_statement_prompt(
                    student_name=student_name,
                    statement_date=statement_date,
                    reflection=reflection,
                    trade_context=trade_context,
                    selected_pcs=selected_pcs,
                )

                system_prompt = prompt_bundle["system_prompt"]
                user_prompt = prompt_bundle["user_prompt"]

                st.write(f"🧠 Prompting {provider} ({target_model})...")
                ai_statement = validate_and_generate(
                    provider=provider,
                    model_name=target_model,
                    api_keys=keys, # Pass the list of keys
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )

                if "API_ERROR" in str(ai_statement):
                    st.error(ai_statement)
                else:
                    st.write("📝 Finalizing first-person perspective and mapping summary...")
                    # Generate mapping summary just like dashboard.py
                    summary_block = "\n\n----- SUMMARY OF CRITERIA COVERED -----\n\n"
                    u_dict = {}
                    for item in selected_pcs:
                        parts = item.split(' - ')
                        if len(parts) >= 3:
                            u_code = parts[0].strip()
                            lo_num = parts[1].strip()
                            pc_code = parts[2].split(':')[0].strip()
                            u_dict.setdefault(u_code, {}).setdefault(lo_num, []).append(pc_code)

                    for u, lo_map in u_dict.items():
                        lo_parts = [f"LO {lo}:{', '.join(pcs)}" for lo, pcs in lo_map.items()]
                        summary_block += f"Unit {u} - {'; '.join(lo_parts)}\n"
                    
                    # Consume platform credit/quota (BYOK is zero-cost).
                    if role != 'admin':
                        allowed, reason = db.consume_ai_credit(
                            st.session_state.org_id, tier, using_byok
                        )
                        if allowed:
                            if reason == "free_credit":
                                st.session_state.credits_balance -= 1
                            elif reason == "platform_quota":
                                st.session_state.ai_quota_used = st.session_state.get("ai_quota_used", 0) + 1
                    
                    st.session_state.current_generated_statement = ai_statement + summary_block
                    status.update(label="✅ Personal Statement Crafted!", state="complete", expanded=False)

    st.caption("⚠️ **Disclaimer:** AI can make mistakes. Please verify that the generated statement accurately reflects your reflection notes.")
    if st.session_state.get('current_generated_statement'):
        db.render_feedback_widget("personal_statement")

    # 4. Display Result and Save Logic
    if 'current_generated_statement' in st.session_state:
        st.markdown("---")
        st.subheader("Preview of Your Statement")
        st.write(st.session_state.current_generated_statement)
        
        # Check lock states
        if st.session_state.get('saving_statement'):
            with st.spinner("Saving statement..."):
                try:
                    user_id = st.session_state.user_session.id
                    unique_units = sorted(list(set([pc.split(' - ')[0] for pc in selected_pcs])))
                    success, err = db.insert_student_statement(
                        user_id=user_id,
                        student_name=student_name,
                        trade_id=trade_id,
                        unit_codes=", ".join(unique_units),
                        reflection_notes=reflection,
                        statement_text=st.session_state.current_generated_statement
                    )
                    if success:
                        st.toast("Statement saved successfully!")
                        del st.session_state.current_generated_statement
                        st.rerun()
                    else:
                        st.error(f"Failed to save: {err}")
                finally:
                    st.session_state.saving_statement = False

        col_save, col_download = st.columns(2)
        with col_save:
            is_saving = st.session_state.get('saving_statement', False)
            if st.button("💾 Save to My Portfolio", disabled=is_saving):
                st.session_state.saving_statement = True
                st.rerun()
        
        with col_download:
            doc_bytes = export_personal_statement_to_word(
                student_name, 
                statement_date, 
                st.session_state.current_generated_statement, 
                selected_pcs=selected_pcs
            )
            st.download_button("📥 Download Word (.docx)", doc_bytes, f"Statement_{student_name}.docx")
