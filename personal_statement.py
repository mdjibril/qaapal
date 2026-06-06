import streamlit as st
import datetime
import database as db
from ai_utils import validate_and_generate
from file_utils import export_personal_statement_to_word

@st.fragment
def render_nos_selection_for_student(nos_data):
    """
    Renders checkboxes for the student to select which PCs they want to include 
    in their personal statement.
    """
    def sync_unit_pcs(u_key, u_data):
        # Callback to update all PCs in a unit when the master checkbox changes
        master_val = st.session_state[f"stmt_unit_all_{u_key}"]
        for lo_pcs in u_data.values():
            for pc in lo_pcs:
                st.session_state[f"stmt_chk_{u_key}_{pc}"] = master_val

    def clear_all_pcs_callback(all_nos_data):
        # Callback to clear all PCs across all units
        for u_key, u_data in all_nos_data.items():
            st.session_state[f"stmt_unit_all_{u_key}"] = False
            for lo_pcs in u_data.values():
                for pc in lo_pcs:
                    st.session_state[f"stmt_chk_{u_key}_{pc}"] = False

    local_selected_pcs = []
    
    unit_titles = list(nos_data.keys())

    # Add a "Clear All" button at the top of the selection area
    st.button(
        "🗑️ Clear All Selections", 
        on_click=clear_all_pcs_callback, 
        args=(nos_data,), 
        key="stmt_clear_all_pcs"
    )

    tabs = st.tabs(unit_titles)
    
    for i, unit_key in enumerate(unit_titles):
        with tabs[i]:
            unit_code = unit_key.split(':')[0]
            # Master checkbox for the entire unit
            st.checkbox(
                f"✅ Select All Performance Criteria for {unit_code}", 
                key=f"stmt_unit_all_{unit_key}",
                on_change=sync_unit_pcs,
                args=(unit_key, nos_data[unit_key])
            )
            
            for lo_key, pcs in nos_data[unit_key].items():
                lo_id = lo_key.split(':')[0].replace("LO", "").strip()
                with st.expander(lo_key):
                    for pc in pcs:
                        if st.checkbox(pc, key=f"stmt_chk_{unit_key}_{pc}"):
                            local_selected_pcs.append(f"{unit_code} - {lo_id} - {pc}")
    
    st.session_state.student_selected_pcs = local_selected_pcs

def main():
    st.title("✍️ Personal Statement of Competence")
    st.info("This tool helps students generate a professional narrative of their achievements based on NSQ standards.")

    # 1. Context Selection
    trade_id = st.session_state.get('selected_trade_id')
    if not trade_id:
        st.warning("Please select a trade in the sidebar to begin.")
        return

    # Access shared session info
    provider = st.session_state.get('ai_provider')
    keys = st.session_state.get('target_keys', []) # Now expects a list of keys
    target_model = st.session_state.get('target_model')

    # 2. Input Section
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Student Full Name", placeholder="e.g. John Doe")
    with col2:
        statement_date = st.date_input("Statement Date", datetime.date.today())

    st.markdown("---")
    st.subheader("Step 1: What did you achieve?")
    
    # Fetch NOS data for selection
    nos_data = db.fetch_nested_nos(trade_id)
    if nos_data:
        render_nos_selection_for_student(nos_data)
    else:
        st.error("No competency data found for the selected trade.")

    st.markdown("---")
    st.subheader("Step 2: Your Reflection")
    reflection = st.text_area(
        "Describe what you did in your own words:",
        placeholder="e.g. I worked on a Dell Optiplex. I had to replace the RAM because the computer was beeping. I used a screwdriver and wore my wrist strap...",
        height=200
    )

    selected_pcs = st.session_state.get('student_selected_pcs', [])
    st.info(f"Selected: {len(selected_pcs)} Performance Criteria")

    st.markdown("---")
    st.subheader("Step 3: Generate Statement")
    
    # Paywall Check
    role = st.session_state.get('user_role')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_out_of_credits = (role != 'admin' and tier == 'free' and credits <= 0)

    if is_out_of_credits:
        selar_base = st.secrets.get("payments", {}).get("selar_link", "https://selar.com/nsqassessment-platformpass")
        user_email = st.session_state.user_session.email
        upgrade_link = f"{selar_base}?email={user_email}"
        st.warning("⚠️ You have 0 credits remaining. Upgrade to the **Platform Pass** to continue generating statements.")
        st.link_button("🚀 Upgrade to Platform Pass", upgrade_link)

    if st.button("Generate My Statement", type="primary", disabled=is_out_of_credits):
        if not reflection:
            st.error("Please provide some reflection notes first.")
        elif not selected_pcs:
            st.error("Please select at least one PC that you achieved.")
        elif provider != "VertexAI" and not keys: # Check if keys list is empty
            if tier == 'free':
                st.error("⛔ Internal AI key missing. Contact administrator.")
            else:
                st.warning("Please enter your AI API key in the sidebar.")
        else:
            with st.status("AI is crafting your professional narrative...", expanded=True) as status:
                st.write("🧵 Weaving reflection notes with competency standards...")
                # --- FIRST-PERSON AI PROMPT ---
                system_prompt = f"""You are a professional mentor helping a student draft their 'Personal Statement of Competence' for an NSQ Portfolio. 
                Your goal is to transform raw reflection notes into a professional narrative written strictly in the FIRST PERSON (using 'I', 'me', 'my').
                
                <strict_rules>
                1. **Perspective**: Strictly FIRST-PERSON singular.
                2. **Tone**: Professional, reflective, and technically confident.
                3. **Volume**: Generate exactly 7 to 8 dense, technical paragraphs.
                4. **Inline Mapping**: Place the mapping inline, immediately after the sentence that demonstrates the criteria, rather than grouping them at the end of the paragraph. Do NOT repeat the Unit code within the same group if multiple criteria from that unit are met in that sentence.
                   Format: (UnitCode - LO#:PC #, #; LO#:PC #, #). Example: (ICT/CMR/005/L2 - LO1:PC 1.1, 1.2).
                5. **Exhaustive Usage**: You MUST integrate every PC provided in the list exactly once.
                6. **Flow**: Create a cohesive narrative story of achievement, not a bulleted list. Explain the 'Why' and 'How' of the actions taken.
                7. **Accessibility**: Use clear English, explaining technical terms simply where necessary.
                8. **Technical Expansion**: DO NOT simply repeat the text of a Performance Criterion. Instead, expand upon it with specific, technically accurate details or examples. For instance, if a criterion mentions identifying security threats, specify types like DDOS, DNS spoofing, or DHCP poisoning to demonstrate deep knowledge.
                </strict_rules>"""

                user_prompt = f"""
                Student Name: {student_name}
                Statement Date: {statement_date}
                Raw Reflection: {reflection}
                Performance Criteria to cover: {", ".join(selected_pcs)}
                
                Write a professional personal statement that weaves all the criteria above into a first-person story of competence."""

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
                    
                    # Deduct credit
                    if role != 'admin' and tier == 'free':
                        db.decrement_credits(st.session_state.org_id)
                        st.session_state.credits_balance -= 1
                    
                    st.session_state.current_generated_statement = ai_statement + summary_block
                    status.update(label="✅ Personal Statement Crafted!", state="complete", expanded=False)

    # 4. Display Result and Save Logic
    if 'current_generated_statement' in st.session_state:
        st.markdown("---")
        st.subheader("Preview of Your Statement")
        st.write(st.session_state.current_generated_statement)
        
        col_save, col_download = st.columns(2)
        with col_save:
            if st.button("💾 Save to My Portfolio"):
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
        
        with col_download:
            doc_bytes = export_personal_statement_to_word(
                student_name, 
                statement_date, 
                st.session_state.current_generated_statement, 
                selected_pcs=selected_pcs
            )
            st.download_button("📥 Download Word (.docx)", doc_bytes, f"Statement_{student_name}.docx")