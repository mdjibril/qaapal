import streamlit as st
import datetime
import database as db
from ai_utils import validate_and_generate
from auth_utils import get_secret
from file_utils import export_witness_to_word
from security_utils import sanitize_text_input, sanitize_notes_input
import components
from prompt_builders import build_witness_statement_prompt

# Criteria selection is now handled by components.render_nos_selection

def main():
    st.title("📑 Witness Testimony / Statement")
    st.info("This page allows a supervisor or expert witness to provide formal evidence of a candidate's competence.")

    trade_id = st.session_state.get('selected_trade_id')
    trade_level_id = st.session_state.get('selected_trade_level_id')
    if not trade_id:
        st.warning("Please select a trade in the sidebar to begin.")
        return

    provider = st.session_state.get('ai_provider')
    keys = st.session_state.get('target_keys', []) # Now expects a list of keys
    target_model = st.session_state.get('target_model')

    st.subheader("Step 1: Witness & Candidate Info")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            raw_witness_name = st.text_input("Witness Name", placeholder="e.g. Engr. Sarah Ahmed")
            witness_name = sanitize_text_input(raw_witness_name, 100)
            raw_witness_role = st.text_input("Job Title / Relationship", placeholder="e.g. Senior Workshop Supervisor")
            witness_role = sanitize_text_input(raw_witness_role, 100)
        with c2:
            raw_candidate_name = st.text_input("Candidate Name", placeholder="e.g. John Doe")
            candidate_name = sanitize_text_input(raw_candidate_name, 100)
            observation_date = st.date_input("Date of Observation", datetime.date.today())

    st.markdown("---")
    st.subheader("Step 2: Competency Mapping")
    nos_data = db.fetch_nested_nos(trade_level_id=trade_level_id, trade_id=trade_id)
    if nos_data:
        components.render_nos_selection(
            nos_data=nos_data,
            prefix="wit_",
            persistent_set_key="persistent_witness_selected_pcs",
            result_list_key="witness_selected_pcs",
            select_key_prefix="wit"
        )
    else:
        st.error("No competency data found.")

    selected_pcs = st.session_state.get('witness_selected_pcs', [])
    st.info(f"Selected: {len(selected_pcs)} Performance Criteria")

    st.markdown("---")
    st.subheader("Step 3: Witness Notes")
    with st.container(border=True):
        raw_witness_notes = st.text_area(
            "Describe what you observed the candidate doing:",
            placeholder="e.g. John correctly identified the fault in the power supply. He used the multimeter safely and followed all workshop protocols...",
            height=150
        )
    witness_notes = sanitize_notes_input(raw_witness_notes, 2000)

    # Paywall Check
    role = st.session_state.get('user_role')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_out_of_credits = (role != 'admin' and tier == 'free' and credits <= 0)

    if is_out_of_credits:
        selar_base = get_secret(["payments", "selar_link"], "payments__selar_link") or "https://selar.com/nsqassessment-platformpass"
        selar_lifetime_base = get_secret(["payments", "selar_lifetime_link"], "payments__selar_lifetime_link") or "https://selar.com/nsqassessment-lifetime"
        user_email = st.session_state.user_session.email
        upgrade_link = f"{selar_base}?email={user_email}"
        lifetime_upgrade_link = f"{selar_lifetime_base}?email={user_email}"
        st.warning("⚠️ You have 0 credits remaining. Upgrade to continue generating testimonies.")
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            st.link_button("🚀 Upgrade to Platform Pass", upgrade_link, width='stretch')
        with col_up2:
            st.link_button("💎 Get Lifetime Tier", lifetime_upgrade_link, width='stretch')

    if st.button("Generate Witness Statement", type="primary", disabled=is_out_of_credits):
        if not witness_notes or not selected_pcs or not witness_name or not candidate_name:
            st.error("Please fill in all details, select at least one PC, and provide observation notes.")
        elif provider != "VertexAI" and not keys: # Check if keys list is empty
            st.warning("Please enter your AI API key(s) in the sidebar.")
        else:
            st.session_state.pop("fb_submitted_witness_statement", None)
            with st.status("Synthesizing formal testimony...", expanded=True) as status:
                st.write("📄 Converting witness notes into formal industrial language...")
                trade_context = st.session_state.get("selected_trade_level_name") or st.session_state.get("selected_trade_name") or 'the specific trade'
                prompt_bundle = build_witness_statement_prompt(
                    witness_name=witness_name,
                    witness_role=witness_role,
                    candidate_name=candidate_name,
                    observation_date=observation_date,
                    witness_notes=witness_notes,
                    trade_context=trade_context,
                    selected_pcs=selected_pcs,
                )

                system_prompt = prompt_bundle["system_prompt"]
                user_prompt = prompt_bundle["user_prompt"]

                st.write(f"🛰️ Dispatching request to {provider}...")
                ai_output = validate_and_generate(
                    provider=provider,
                    model_name=target_model,
                    api_keys=keys, # Pass the list of keys
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )

                if "API_ERROR" in str(ai_output):
                    st.error(ai_output)
                else:
                    st.write("✅ Validating third-person tone and cross-referencing criteria...")
                    # Generate mapping summary block
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
                    
                    # Deduct credit
                    if role != 'admin' and tier == 'free':
                        db.decrement_credits(st.session_state.org_id)
                        st.session_state.credits_balance -= 1
                    
                    st.session_state.current_witness_statement = ai_output + summary_block
                    status.update(label="✅ Witness Statement Ready!", state="complete", expanded=False)

    st.caption("⚠️ **Disclaimer:** AI can make mistakes. Please verify that the generated testimony accurately reflects your observation notes.")
    if st.session_state.get('current_witness_statement'):
        db.render_feedback_widget("witness_statement")

    if 'current_witness_statement' in st.session_state:
        st.markdown("---")
        st.subheader("Preview & Finalize")
        st.write(st.session_state.current_witness_statement)
        
        # Check lock states
        if st.session_state.get('saving_witness'):
            with st.spinner("Saving witness testimony..."):
                unique_units = sorted(list(set([pc.split(' - ')[0] for pc in selected_pcs])))
                success, err = db.insert_witness_statement(
                    user_id=st.session_state.user_session.id,
                    witness_name=witness_name,
                    witness_role=witness_role,
                    candidate_name=candidate_name,
                    trade_id=trade_id,
                    unit_codes=", ".join(unique_units),
                    witness_notes=witness_notes,
                    statement_text=st.session_state.current_witness_statement
                )
                st.session_state.saving_witness = False
                if success:
                    st.toast("Witness statement saved successfully!")
                    del st.session_state.current_witness_statement
                    st.rerun()
                else:
                    st.error(f"Error saving: {err}")

        col_save, col_word = st.columns(2)
        with col_save:
            is_saving = st.session_state.get('saving_witness', False)
            if st.button("💾 Save to Database", disabled=is_saving):
                st.session_state.saving_witness = True
                st.rerun()
        
        with col_word:
            doc_bytes = export_witness_to_word(
                witness_name, witness_role, candidate_name, observation_date, 
                st.session_state.current_witness_statement, selected_pcs
            )
            st.download_button("📥 Download Word (.docx)", doc_bytes, f"Witness_{candidate_name}.docx")
