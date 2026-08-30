import streamlit as st
import datetime
import time
from file_utils import export_to_word
from ai_utils import validate_and_generate, transcribe_audio_with_vertex
from auth_utils import get_secret
from security_utils import sanitize_text_input, sanitize_notes_input
import database as db
import components
from prompt_builders import build_dashboard_prompt
from app_state import ensure_session_defaults

# Criteria selection is now handled by components.render_nos_selection

def main():
    ensure_session_defaults(
        {
            "last_request_time": 0,
            "dash_atmosphere": lambda: st.session_state.get("default_env_text", ""),
        }
    )

    # --- UI DESIGN ---
    st.title("📝 NSQ Report Generator")
    
    trade_id = st.session_state.get('selected_trade_id')
    trade_level_id = st.session_state.get('selected_trade_level_id')
    provider = st.session_state.get('ai_provider')
    keys = st.session_state.get('target_keys', []) # Now expects a list of keys
    target_model = st.session_state.get('target_model')
    assessor_name = st.session_state.get('assessor_name', 'Jibril Dauda Muhammad')
    # assessor_id = st.session_state.get('assessor_id', 'QAA/XXXX/ICT')
    dev_mode = st.session_state.get('dev_mode', False)

    user_id = st.session_state.user_session.id
    role = st.session_state.user_role
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_out_of_credits = (role != 'admin' and tier == 'free' and credits <= 0)
    
    # st.write(f"Logged in as: {st.session_state.user_session.email}")
    # st.write(f"User ID: {user_id}")
    # st.write(f"User Role: {role}")
    # # st.write(f"Raw Data found: {len(reports)} records")

    if not trade_id:
        st.warning("Please select a trade in the sidebar.")
        return

    # 3. UI Section
    st.markdown("#### Step 1: Student & Session Info")
    with st.expander("Step 1: Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            raw_student_name = st.text_input("Candidate Name", key="dash_candidate_name")
            student_name = sanitize_text_input(raw_student_name, 100)
            assessment_date = st.date_input("Assessment Date", datetime.date.today(), key="dash_assessment_date")
        with col2:
            raw_time_frame = st.text_input("Timeline", placeholder="e.g. 9:00AM – 12:00PM", key="dash_timeline")
            time_frame = sanitize_text_input(raw_time_frame, 100)
            raw_atmosphere = st.text_area("Atmospheric Details", key="dash_atmosphere")
            atmosphere = sanitize_notes_input(raw_atmosphere, 500)

    
    st.markdown("#### Step 2: Select Achieved PCs")

    trade_id = st.session_state.get('selected_trade_id')
    trade_level_id = st.session_state.get('selected_trade_level_id')
    NOS_DATA = db.fetch_nested_nos(trade_level_id=trade_level_id, trade_id=trade_id) 

    if not NOS_DATA:
        st.warning(f"No units found for trade ID {trade_id}.")
    else:
        # --- ADMIN-ONLY: Assessment Templates ---
        if role == 'admin':
            st.markdown("##### 📋 Assessment Templates (Admin Only)")
            templates = db.fetch_assessment_templates(trade_id=trade_id, trade_level_id=trade_level_id)
            if templates:
                template_names = {t['id']: t['name'] for t in templates}
                selected_template_id = st.selectbox(
                    "Load a template to pre-fill PC selections",
                    options=list(template_names.keys()),
                    format_func=lambda x: template_names[x],
                    key="admin_template_select"
                )
                if st.button("Load Template", key="load_template_btn"):
                    template = next((t for t in templates if t['id'] == selected_template_id), None)
                    if template:
                        pc_ids = template.get('pc_ids', [])
                        # Pre-check these PCs in the persistent set
                        st.session_state.persistent_selected_pcs = set(pc_ids)
                        st.rerun()
            else:
                st.caption("No templates saved yet for this trade/level.")

        # Call the fragment
        components.render_nos_selection(
            nos_data=NOS_DATA,
            prefix="",
            persistent_set_key="persistent_selected_pcs",
            result_list_key="current_selected_pcs",
            select_key_prefix="dash"
        )

        # --- ADMIN-ONLY: Save Current Selection as Template ---
        if role == 'admin':
            current_selected = st.session_state.get('current_selected_pcs', [])
            if current_selected:
                with st.expander("💾 Save Current Selection as Template"):
                    template_name = st.text_input("Template Name", key="save_template_name")
                    if st.button("Save Template", key="save_template_btn"):
                        if template_name.strip():
                            result, err = db.save_assessment_template(
                                name=template_name.strip(),
                                trade_id=trade_id,
                                trade_level_id=trade_level_id,
                                pc_ids=current_selected,
                                user_id=user_id
                            )
                            if result:
                                st.toast("Template saved.")
                                st.rerun()
                            else:
                                st.error(f"Failed to save template: {err}")
                        else:
                            st.error("Template name is required.")

    st.markdown("#### Step 3: Unique Learning Moment")
    st.info("""
    **💡 Pro-Tip for Unique Reports:** Use the 'Observation Formula' for better AI results:
    **[Action]** + **[Specific Tool/Component]** + **[Specific Result or Quote]**
    *Example: 'Struggled with the RJ45 crimping tool at first but corrected the pin alignment manually after a second attempt.'*
    """)

    # --- ADMIN-ONLY: Voice Dictation ---
    if role == 'admin':
        with st.expander("🎤 Voice Dictation (Admin Only)", expanded=False):
            audio_bytes = st.audio_input("Record observation notes by voice")
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
                if st.button("Transcribe Audio", key="transcribe_btn"):
                    with st.spinner("Transcribing..."):
                        transcript, err = transcribe_audio_with_vertex(audio_bytes)
                        if transcript:
                            st.session_state.observation_notes_input = transcript
                            st.toast("Transcription complete.")
                            st.rerun()
                        else:
                            st.error(f"Transcription failed: {err}")

    # --- ADMIN-ONLY: Evidence Matrix Auto-Mapper ---
    if role == 'admin':
        if st.button("✨ Suggest PCs from Notes", key="suggest_pcs_btn"):
            current_notes = st.session_state.get('observation_notes_input', '')
            if not current_notes.strip():
                st.warning("Please enter observation notes first (Step 3).")
            else:
                with st.spinner("Analyzing notes and suggesting PCs..."):
                    pc_list = []
                    for unit_key, los in NOS_DATA.items():
                        unit_code = unit_key.split(':')[0]
                        for lo_key, pcs in los.items():
                            lo_id = lo_key.split(':')[0].replace("LO", "").strip()
                            for pc in pcs:
                                pc_list.append(f"{unit_code} - {lo_id} - {pc}")

                    suggestion_prompt = f"""
Given the following observation notes:
{current_notes}

And the following available Performance Criteria:
{chr(10).join(pc_list)}

Return a JSON array of the PC strings that are demonstrably evidenced in the notes. Only include PCs where the notes clearly describe the action or outcome. Return ONLY the JSON array, nothing else.
"""
                    suggestion = validate_and_generate(
                        provider=provider,
                        model_name=target_model,
                        api_keys=keys,
                        prompt=suggestion_prompt,
                        system_prompt="You are a PC matching engine. Return only valid JSON arrays."
                    )
                    if isinstance(suggestion, str) and "API_ERROR" not in suggestion:
                        import json
                        try:
                            suggested_pcs = json.loads(suggestion)
                            st.session_state.persistent_selected_pcs = set(suggested_pcs)
                            st.toast(f"Suggested {len(suggested_pcs)} PCs.")
                            st.rerun()
                        except Exception:
                            st.error(f"Failed to parse AI suggestion: {suggestion}")
                    else:
                        st.error(f"PC suggestion failed: {suggestion}")

    raw_learning_moment = st.text_area(
        "Observation Notes", 
        placeholder="What did this specific student do, say, or struggle with during this session?",
        height=150,
        help="This is the 'flavor' that makes this report different from the others. Even 1-2 sentences here will make the AI output much more realistic.",
        key="observation_notes_input"
    )
    learning_moment = sanitize_notes_input(raw_learning_moment, 2000)

    # 3. Synchronize selected PCs from the fragment state
    selected_pcs = st.session_state.get('current_selected_pcs', [])
    st.info(f"Selected: {len(selected_pcs)} Performance Criteria")

    # --- GENERATION LOGIC ---
    if is_out_of_credits:
        selar_base = get_secret(["payments", "selar_link"], "payments__selar_link") or "https://selar.com/nsqassessment-platformpass"
        selar_lifetime_base = get_secret(["payments", "selar_lifetime_link"], "payments__selar_lifetime_link") or "https://selar.com/nsqassessment-lifetime"
        credit_20 = get_secret(["payments", "selar_credit_20"], "payments__selar_credit_20")
        credit_150 = get_secret(["payments", "selar_credit_150"], "payments__selar_credit_150")
        credit_400 = get_secret(["payments", "selar_credit_400"], "payments__selar_credit_400")
        user_email = st.session_state.user_session.email
        upgrade_link = f"{selar_base}?email={user_email}"
        lifetime_upgrade_link = f"{selar_lifetime_base}?email={user_email}"
        credit_20_link = f"{credit_20}?email={user_email}" if credit_20 else None
        credit_150_link = f"{credit_150}?email={user_email}" if credit_150 else None
        credit_400_link = f"{credit_400}?email={user_email}" if credit_400 else None

        st.warning("⚠️ You have 0 AI credits remaining. Buy a credit pack or upgrade to continue.")

        st.markdown("**⚡ Quick AI Credit Packs**")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            if credit_20_link:
                st.link_button("₦1,000 — 20 Reports", credit_20_link, width='stretch')
        with col_c2:
            if credit_150_link:
                st.link_button("₦5,000 — 150 Reports", credit_150_link, width='stretch')
        with col_c3:
            if credit_400_link:
                st.link_button("₦10,000 — 400 Reports", credit_400_link, width='stretch')

        st.markdown("**Or Upgrade Your Plan**")
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            st.link_button("🚀 Upgrade to Platform Pass", upgrade_link, width='stretch')
        with col_up2:
            st.link_button("💎 Get Lifetime Tier", lifetime_upgrade_link, width='stretch')

    if st.button("Generate & Finalize Report", disabled=is_out_of_credits):
        current_time = time.time()
        time_passed = current_time - st.session_state.last_request_time
 
        if not dev_mode and time_passed < 10:
            st.warning(f"🕒 Rate Limit Protection: Wait {int(10 - time_passed)}s.")
        elif not student_name.strip():
            st.error("⚠️ **Candidate Name** is required. Please fill in Step 1 before generating.")
        elif not time_frame.strip():
            st.error("⚠️ **Timeline** is required. Please fill in Step 1 before generating (e.g. 9:00AM – 12:00PM).")
        elif not atmosphere.strip():
            st.error("⚠️ **Atmospheric Details** is required. Please describe the session environment in Step 1.")
        elif not learning_moment.strip():
            st.error("⚠️ **Observation Notes** (Step 3) cannot be empty. Describe what the candidate did during the session.")
        elif not selected_pcs:
            st.warning("Please select at least one Performance Criterion above.")
        elif not dev_mode and provider != "VertexAI" and not keys: # Check if keys list is empty
            st.warning(f"Please enter the {provider} API key(s) in the sidebar.")
        else:
            for key in (
                "current_assessment_report",
                "fb_submitted_dashboard",
                "fb_comment_input_dashboard",
            ):
                st.session_state.pop(key, None)
            st.session_state.last_request_time = current_time
            with st.status(f"Using {provider} ({target_model}) to synthesize...", expanded=True) as status:
                st.write("🔍 Preparing assessment context and mapping criteria...")
                
                unique_units = list(set([pc.split(' - ')[0] for pc in selected_pcs]))
                unit_header_info = "\n".join(unique_units)
                detailed_criteria_text = "\n".join(selected_pcs)
                formatted_date = assessment_date.strftime("%B %d, %Y")
                candidate_first_name = student_name.strip().split()[0]

                trade_context = st.session_state.get("selected_trade_level_name") or st.session_state.get("selected_trade_name") or "the specific trade"
                prompt_bundle = build_dashboard_prompt(
                    student_name=student_name,
                    assessment_date=assessment_date,
                    time_frame=time_frame,
                    atmosphere=atmosphere,
                    trade_context=trade_context,
                    learning_moment=learning_moment,
                    selected_pcs=selected_pcs,
                )

                system_prompt = prompt_bundle["system_prompt"]
                user_prompt = prompt_bundle["user_prompt"]

                if dev_mode:
                    ai_narrative = "DEV MODE: AI was skipped. Database and Word functions work."
                else:
                    st.write(f"🤖 Transmitting to {provider} for synthesis...")
                    ai_narrative = validate_and_generate(
                        provider=provider, 
                        model_name=target_model, 
                        api_keys=keys, # Pass the list of keys
                        prompt=user_prompt, 
                        system_prompt=system_prompt
                    )

                if isinstance(ai_narrative, str) and "API_ERROR" in ai_narrative:
                    st.error(ai_narrative)
                else:
                    st.write("📊 Generating criteria summary block...")
                    summary_block = "\n\n----- SUMMARY OF CRITERIA COVERED -----\n\n"
                    u_dict = {}
                    for item in selected_pcs: # Format: "Unit - LO - PC"
                        parts = item.split(' - ')
                        if len(parts) >= 3:
                            u_code = parts[0].strip()
                            lo_num = parts[1].strip()
                            pc_code = parts[2].split(':')[0].strip()
                            u_dict.setdefault(u_code, {}).setdefault(lo_num, []).append(pc_code)

                    for u, lo_map in u_dict.items():
                        lo_parts = [f"LO {lo}:{', '.join(pcs)}" for lo, pcs in lo_map.items()]
                        summary_block += f"Unit {u} - {'; '.join(lo_parts)}\n"
                    
                    # Deduct credit for free tier users upon successful generation
                    if role != 'admin' and tier == 'free':
                        db.decrement_credits(st.session_state.org_id)
                        st.session_state.credits_balance -= 1
                    
                    full_report_text = ai_narrative + summary_block
                    st.session_state['current_assessment_report'] = full_report_text

                    # Attempt Database Save
                    st.write("💾 Finalizing report and saving to Database...")
                    success, result = db.insert_report(
                        student_name, 
                        trade_id, 
                        ", ".join(u_dict.keys()),  
                        full_report_text, 
                        assessment_date,
                        user_id 
                    )
                    
                    if success:
                        st.success("✅ SUCCESS: Report saved to Database!")
                        
                        # --- AUTO-TRACK PORTFOLIO PROGRESS (admin-only) ---
                        if role == 'admin':
                            report_id = result.get('id') if isinstance(result, dict) else None
                            if report_id and selected_pcs:
                                st.write("🔄 Auto-tracking PC progress for student portfolio...")
                                found, tracked_count, track_err = db.auto_track_portfolio_progress(
                                    student_name=student_name,
                                    trade_id=trade_id,
                                    trade_level_id=trade_level_id,
                                    selected_pcs=selected_pcs,
                                    evidence_report_id=report_id,
                                    assessed_by=user_id
                                )
                                if found:
                                    st.toast(f"Tracked {tracked_count} PCs for {student_name}.")
                                else:
                                    st.warning(f"No matching portfolio found for {student_name} in this trade. Progress was NOT tracked.")
                                    if track_err:
                                        st.error(track_err)
                    else:
                        st.error(f"❌ DATABASE ERROR: {result}")
                        st.warning("Verify that the 'assessment_reports' table contains a 'created_by' column.")

                    st.markdown("### Preview")
                    st.info(full_report_text)
                    doc_bytes = export_to_word(
                        student_name, 
                        assessment_date, 
                        full_report_text, 
                        assessor_name,
                        timeline=time_frame,
                        atmosphere=atmosphere,
                        selected_pcs=selected_pcs
                    )
                    
                    c1, c2 = st.columns(2)
                    with c1: st.download_button("📥 Word (.docx)", data=doc_bytes, file_name=f"NSQ_{student_name}.docx")
                    with c2: st.download_button("Download Text (.txt)", full_report_text, file_name=f"{student_name}.txt")

    st.caption("⚠️ **Disclaimer:** AI can make mistakes. Please verify that the generated report accurately reflects your field observation notes.")
    if st.session_state.get('current_assessment_report'):
        db.render_feedback_widget("dashboard")

# --- IMPORTANT: ADD THIS AT THE BOTTOM ---
if __name__ == "__main__":
    main()
