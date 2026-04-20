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
        elif not key and not dev_mode:
            st.warning(f"Please enter the {provider} API key in the sidebar.")
        else:
            st.session_state.last_request_time = current_time
            with st.spinner(f"Using {provider} ({target_model}) to synthesize..."):
                
                unique_units = list(set([pc.split(' - ')[0] for pc in selected_pcs]))
                unit_header_info = "\n".join(unique_units)
                detailed_criteria_text = "\n".join(selected_pcs)
                formatted_date = assessment_date.strftime("%B %d, %Y")

                prompt = f"""
                You are a Lead NSQ Assessor. Write a high-level technical narrative for {student_name}.

                REPORT CONTEXT:
                - Assessor: {assessor_name} ({assessor_id})
                - Date: {formatted_date}
                - Units: {unit_header_info}
                - Environment: {atmosphere}
                - The "Hook" (Breaktrough moment): {learning_moment}

                CRITERIA TO INTEGRATE (The Ingredients):
                {detailed_criteria_text}

                STRICT NARRATIVE RULES:
                1. NO STAGED SEQUENCING: Do not write one paragraph per PC. A single paragraph should naturally weave together 2 or 3 related or non-related PCs.
                2. CONTINUOUS FLOW: The report must read like a professional "day-in-the-life" observation. Use phrases like "Simultaneously," "This led the candidate to," or "Building on the previous step.", {student_name} commenced the session at {time_frame}, {student_name} ended the session at {time_frame}.
                3. MINIMUM 8 PARAGRAPHS: Each paragraph must be dense and technical.
                4. MAXIMUM 10 PARAGRAPHS: Do not exceed 10 paragraphs. Be concise but exhaustive.
                5. MAXIMUM PAGES: The final report should not exceed 2 pages when formatted in Word with standard margins and font size.
                6. MAXIMIZE CRITERIA INTEGRATION: Each paragraph should integrate multiple PCs, showing how the candidate's actions and explanations naturally covered several criteria at once.
                7. MAPPING: Use grouped shorthand at the end of paragraphs. 
                Example: (Unit 11-PC 5.1, 5.2, 5.4).
                8. THE HOOK: Do not just "mention" the {learning_moment}; make it a central part of the story where multiple criteria were met during that specific breakthrough.
                9. AVOID PLACEHOLDERS: Use the provided date and names.
                10. TONE: The narrative should be formal, technical, and exhaustive, suitable for a professional assessment report.
                11. DO NOT REPEAT CRITERIA: Each PC should only be referenced once in the narrative, but can be grouped with related PCs for a more natural flow.
                12. USE ALL PROVIDED CRITERIA: Ensure that every PC in the detailed list is integrated into the narrative, either directly or through inference based on the candidate's actions and explanations.
                13. NO HALLUCINATION: Do not invent PC numbers outside of the provided list.
                14. SHOW, DON'T TELL: Instead of saying "the candidate was competent," describe what the candidate did that demonstrated competence, and link those actions to the PCs.
                15. DONT USE HEAVY DICTIONARY LANGUAGE: The report should be professional but also clear and straightforward. Avoid overly complex sentences that could obscure the candidate's actual performance and the criteria met.
                16. DONT USE HEAVY DICTIONARY LANGUAGE: The report should be professional and naturally depict step by step procedure of what the candidate will ordinarl do to acheive the performance criteria. noting the candiddate is under direct observation by a quality assurance assesscor
                17. **READER UNDERSTANDING:** The report should be written so that a reader can easily understand how the candidate's actions and explanations during the session directly relate to the specific performance criteria.
                18. **SEAMLESS INTEGRATION:** The narrative should seamlessly integrate the criteria into the story of the candidate's performance, making it clear how each criterion was met through their actions and decisions throughout the session, without needing to cross-reference a separate list.
                19. **COMPREHENSIVE DETAIL:** The narrative should be detailed enough to provide a comprehensive picture of the candidate's performance, including any challenges they faced and how they overcame them, while also clearly demonstrating how they met the required performance criteria in a way that would be evident to an assessor reviewing the report for assessment purposes.
                20. **COHERENT FLOW:** The paragraphs should be linked together to form a coherent narrative.
                """

                if dev_mode:
                    ai_narrative = "DEV MODE: AI was skipped. Database and Word functions work."
                else:
                    ai_narrative = validate_and_generate(provider, target_model, key, prompt)

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