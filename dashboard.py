import streamlit as st
import datetime
import time
from file_utils import export_to_word
from ai_utils import validate_and_generate
import database as db

@st.fragment
def render_nos_selection(nos_data):
    """
    Renders checkboxes in a fragment so clicking 
    doesn't trigger a full-page reload/faint.
    """
    local_selected_pcs = []
    
    # Generate Tabs based on Units
    unit_titles = list(nos_data.keys())
    tabs = st.tabs(unit_titles)
    
    for i, unit_key in enumerate(unit_titles):
        with tabs[i]:
            for lo_key, pcs in nos_data[unit_key].items():
                with st.expander(lo_key):
                    for pc in pcs:
                        # Unique key is vital to keep checkbox state
                        if st.checkbox(pc, key=f"chk_{unit_key}_{pc}"):
                            # Standardizing the string for the report
                            unit_code = unit_key.split(':')[0]
                            local_selected_pcs.append(f"{unit_code} - {pc}")
    
    # Store the results in session state so the "Generate" button can access them
    st.session_state.current_selected_pcs = local_selected_pcs

def main():

    if 'last_request_time' not in st.session_state:
        st.session_state.last_request_time = 0

    # --- UI DESIGN ---
    st.title("📝 NSQ Report Generator")
    
    trade_id = st.session_state.get('selected_trade_id')
    provider = st.session_state.get('ai_provider')
    key = st.session_state.get('target_key')
    target_model = st.session_state.get('target_model')
    atmosphere = st.session_state.get('default_env_text', '')
    assessor_name = st.session_state.get('assessor_name', 'Jibril Dauda Muhammad')
    assessor_id = st.session_state.get('assessor_id', 'QAA/XXXX/ICT')
    dev_mode = st.session_state.get('dev_mode', False)

    user_id = st.session_state.user_session.id
    role = st.session_state.user_role
    
    # st.write(f"Logged in as: {st.session_state.user_session.email}")
    # st.write(f"User ID: {user_id}")
    # st.write(f"User Role: {role}")
    # # st.write(f"Raw Data found: {len(reports)} records")

    if not trade_id:
        st.warning("Please select a trade in the sidebar.")
        return


    # 3. Fetch Data
    NOS_DATA = db.fetch_nested_nos(trade_id)
    
    # 4. UI Section
    st.markdown("#### Step 1: Student & Session Info")
    with st.expander("Step 1: Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("Candidate Name")
            assessment_date = st.date_input("Assessment Date", datetime.date.today())
        with col2:
            time_frame = st.text_input("Timeline", placeholder="e.g. 9:00AM – 12:00PM")
            atmosphere = st.text_area("Atmospheric Details", value=atmosphere)

    
    st.markdown("#### Step 2: Select Achieved PCs")

    trade_id = st.session_state.get('selected_trade_id')
    # Ensure db.fetch_nested_nos has @st.cache_data in your database.py file!
    NOS_DATA = db.fetch_nested_nos(trade_id) 

    if not NOS_DATA:
        st.warning(f"No units found for trade ID {trade_id}.")
    else:
        # 2. Call the fragment
        render_nos_selection(NOS_DATA)

    st.markdown("#### Step 3: Unique Learning Moment")
    # The Formula Guide (A visual reminder for the user)
    st.info("""
    **💡 Pro-Tip for Unique Reports:** Use the 'Observation Formula' for better AI results:
    **[Action]** + **[Specific Tool/Component]** + **[Specific Result or Quote]**
    *Example: 'Struggled with the RJ45 crimping tool at first but corrected the pin alignment manually after a second attempt.'*
    """)

    learning_moment = st.text_area(
        "Observation Notes", 
        placeholder="What did this specific student do, say, or struggle with during this session?",
        height=150,
        help="This is the 'flavor' that makes this report different from the others. Even 1-2 sentences here will make the AI output much more realistic."
    )

    # 3. Synchronize selected PCs from the fragment state
    selected_pcs = st.session_state.get('current_selected_pcs', [])
    st.info(f"Selected: {len(selected_pcs)} Performance Criteria")

    # --- GENERATION LOGIC ---
    if st.button("Generate & Finalize Report"):
        current_time = time.time()
        time_passed = current_time - st.session_state.last_request_time
        
        if not dev_mode and time_passed < 10:
            st.warning(f"🕒 Rate Limit Protection: Wait {int(10 - time_passed)}s.")
        elif not selected_pcs:
            st.warning("Please select at least one Performance Criterion above.")
        elif not dev_mode and not key:
            st.warning(f"Please enter the {provider} API key in the sidebar.")
        else:
            st.session_state.last_request_time = current_time
            with st.spinner(f"Using {provider} ({target_model}) to synthesize..."):
                
                unique_units = list(set([pc.split(' - ')[0] for pc in selected_pcs]))
                unit_header_info = "\n".join(unique_units)
                detailed_criteria_text = "\n".join(selected_pcs)
                formatted_date = assessment_date.strftime("%B %d, %Y")

                system_prompt = f"""You are a Lead NSQ Assessor. Your goal is to write high-level technical narratives that are professional, exhaustive, and map strictly to performance criteria.

                <strict_rules>
                ### NARRATIVE STRUCTURE & FLOW
                1. **The Timeline**: State clearly that the session commenced at {time_frame} and concluded at {time_frame}.
                2. **Continuous Flow**: Write a "day-in-the-life" professional observation. Use logical transitions (e.g., "Building on this," "Simultaneously," "This led to"). 
                3. **Volume**: Generate exactly 7 to 9 dense, technical paragraphs. The final output must fit within 2 standard pages.
                4. **The Hook**: Integrate the breakthrough moment ({learning_moment}) as a central narrative peak where multiple criteria were met simultaneously.

                ### CRITERIA INTEGRATION RULES
                5. **No Staged Sequencing**: Do NOT write one paragraph per PC. Weave 2-3 PCs naturally into every paragraph.
                6. **Show, Don't Tell**: Instead of stating "the candidate is competent," describe specific technical actions and decisions that prove competence.
                7. **Mapping**: At the end of every paragraph, list the met criteria in shorthand grouping. Example: (Unit 11-PC 5.1, 5.2).
                8. **Exhaustive Usage**: You MUST use every PC provided in the user's list exactly once. Do not hallucinate or invent PC codes.
                9. **Seamlessness**: The reader should understand how the action meets the PC without needing a cross-reference list.
                
                ### TONE & LANGUAGE
                10. **Professionalism**: Maintain a formal, technical tone.
                11. **Clarity**: Avoid "dictionary-heavy" or overly flowery language. Focus on clear, straightforward procedural descriptions of what the candidate did under direct observation.
                12. **Coherence**: Ensure each paragraph links logically to the next to form a unified story of the assessment session.
                </strict_rules>

                <example_paragraph>
                While navigating the server room environment, the candidate demonstrated high awareness of safety protocols by ensuring all external power cables were disconnected before opening the chassis. Simultaneously, they utilized an anti-static wrist strap to ground themselves, effectively mitigating the risk of ESD damage to the sensitive motherboard components. (ICT/CMR/004/L2-PC 1.2, 1.3).
                </example_paragraph>"""

                user_prompt = f"""Write the NSQ assessment report for {student_name}.

                <report_context>
                Candidate: {student_name}
                Assessor: {assessor_name} ({assessor_id})
                Date: {formatted_date}
                Environment: {atmosphere}
                Breakthrough Moment: {learning_moment}
                Units: {unit_header_info}
                </report_context>

                <performance_criteria_to_integrate>
                {detailed_criteria_text}
                </performance_criteria_to_integrate>

                Ensure every single PC listed above is integrated into the narrative exactly once."""

                if dev_mode:
                    ai_narrative = "DEV MODE: AI was skipped. Database and Word functions work."
                else:
                    ai_narrative = validate_and_generate(
                        provider=provider, 
                        model_name=target_model, 
                        api_key=key, 
                        prompt=user_prompt, 
                        system_prompt=system_prompt
                    )

                if isinstance(ai_narrative, str) and "API_ERROR" in ai_narrative:
                    st.error(ai_narrative)
                else:
                    summary_block = "\n\n----- SUMMARY OF CRITERIA COVERED -----\n\n"
                    u_dict = {}
                    for item in selected_pcs:
                        u_code = item.split(' - ')[0].split(':')[0]
                        pc_code = item.split(' - ')[1].split(':')[0]
                        if u_code not in u_dict: u_dict[u_code] = []
                        u_dict[u_code].append(pc_code)
                    for u, pc_list in u_dict.items():
                        summary_block += f"{u}: {', '.join(pc_list)}\n"
                    
                    full_report_text = ai_narrative + summary_block

                    # Attempt Database Save
                    with st.spinner("Saving report to Supabase..."):
                        success, error_msg = db.insert_report(
                            student_name, 
                            trade_id, 
                            ", ".join(u_dict.keys()),  
                            full_report_text, 
                            assessment_date,
                            user_id 
                        )
                    
                        if success:
                            st.success("✅ SUCCESS: Report saved to Supabase!")
                        else:
                            st.error(f"❌ DATABASE ERROR: {error_msg}")
                            st.warning("Verify that the 'assessment_reports' table contains a 'created_by' column.")

                    st.markdown("### Preview")
                    st.info(full_report_text)
                    doc_bytes = export_to_word(
                        student_name, 
                        assessment_date, 
                        full_report_text, 
                        assessor_name, 
                        assessor_id,
                        timeline=time_frame,
                        atmosphere=atmosphere,
                        selected_pcs=selected_pcs
                    )
                    
                    c1, c2 = st.columns(2)
                    with c1: st.download_button("📥 Word (.docx)", data=doc_bytes, file_name=f"NSQ_{student_name}.docx")
                    with c2: st.download_button("Download Text (.txt)", full_report_text, file_name=f"{student_name}.txt")


# --- IMPORTANT: ADD THIS AT THE BOTTOM ---
if __name__ == "__main__":
    main()