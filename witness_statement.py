import streamlit as st
import datetime
import database as db
from ai_utils import validate_and_generate
from file_utils import export_witness_to_word

@st.fragment
def render_nos_selection_for_witness(nos_data):
    """
    Renders checkboxes for the witness to select which PCs were observed.
    """
    def sync_unit_pcs(u_key, u_data):
        master_val = st.session_state[f"wit_unit_all_{u_key}"]
        for lo_pcs in u_data.values():
            for pc in lo_pcs:
                st.session_state[f"wit_chk_{u_key}_{pc}"] = master_val

    def clear_all_pcs_callback(all_nos_data):
        for u_key, u_data in all_nos_data.items():
            st.session_state[f"wit_unit_all_{u_key}"] = False
            for lo_pcs in u_data.values():
                for pc in lo_pcs:
                    st.session_state[f"wit_chk_{u_key}_{pc}"] = False

    local_selected_pcs = []
    unit_titles = list(nos_data.keys())

    st.button("🗑️ Clear All Selections", on_click=clear_all_pcs_callback, args=(nos_data,), key="wit_clear_all_pcs")

    tabs = st.tabs(unit_titles)
    for i, unit_key in enumerate(unit_titles):
        with tabs[i]:
            unit_code = unit_key.split(':')[0]
            st.checkbox(f"✅ Observed all for {unit_code}", key=f"wit_unit_all_{unit_key}", on_change=sync_unit_pcs, args=(unit_key, nos_data[unit_key]))
            
            for lo_key, pcs in nos_data[unit_key].items():
                lo_id = lo_key.split(':')[0].replace("LO", "").strip()
                with st.expander(lo_key):
                    for pc in pcs:
                        if st.checkbox(pc, key=f"wit_chk_{unit_key}_{pc}"):
                            local_selected_pcs.append(f"{unit_code} - {lo_id} - {pc}")
    
    st.session_state.witness_selected_pcs = local_selected_pcs

def main():
    st.title("📑 Witness Testimony / Statement")
    st.info("This page allows a supervisor or expert witness to provide formal evidence of a candidate's competence.")

    trade_id = st.session_state.get('selected_trade_id')
    if not trade_id:
        st.warning("Please select a trade in the sidebar to begin.")
        return

    provider = st.session_state.get('ai_provider')
    keys = st.session_state.get('target_keys', []) # Now expects a list of keys
    target_model = st.session_state.get('target_model')

    st.subheader("Step 1: Witness & Candidate Info")
    c1, c2 = st.columns(2)
    with c1:
        witness_name = st.text_input("Witness Name", placeholder="e.g. Engr. Sarah Ahmed")
        witness_role = st.text_input("Job Title / Relationship", placeholder="e.g. Senior Workshop Supervisor")
    with c2:
        candidate_name = st.text_input("Candidate Name", placeholder="e.g. John Doe")
        observation_date = st.date_input("Date of Observation", datetime.date.today())

    st.markdown("---")
    st.subheader("Step 2: Competency Mapping")
    nos_data = db.fetch_nested_nos(trade_id)
    if nos_data:
        render_nos_selection_for_witness(nos_data)
    else:
        st.error("No competency data found.")

    selected_pcs = st.session_state.get('witness_selected_pcs', [])
    st.info(f"Selected: {len(selected_pcs)} Performance Criteria")

    st.markdown("---")
    st.subheader("Step 3: Witness Notes")
    witness_notes = st.text_area(
        "Describe what you observed the candidate doing:",
        placeholder="e.g. John correctly identified the fault in the power supply. He used the multimeter safely and followed all workshop protocols...",
        height=150
    )

    # Paywall Check
    role = st.session_state.get('user_role')
    tier = st.session_state.get('subscription_tier', 'free')
    credits = st.session_state.get('credits_balance', 0)
    is_out_of_credits = (role != 'admin' and tier == 'free' and credits <= 0)

    if is_out_of_credits:
        st.warning("⚠️ You have 0 credits remaining. Upgrade to the **Platform Pass** to continue generating testimonies.")

    if st.button("Generate Witness Statement", type="primary", disabled=is_out_of_credits):
        if not witness_notes or not selected_pcs or not witness_name or not candidate_name:
            st.error("Please fill in all details, select at least one PC, and provide observation notes.")
        elif is_out_of_credits:
            db.mock_payment_dialog(st.session_state.org_id)
        elif provider != "VertexAI" and not keys: # Check if keys list is empty
            st.warning("Please enter your AI API key(s) in the sidebar.")
        else:
            with st.spinner("Synthesizing formal testimony..."):
                system_prompt = f"""You are a professional industrial supervisor writing an NSQ Witness Statement.
                Your goal is to transform raw observation notes into a formal, objective, and validating testimony that maps to specific competency standards.
                
                <strict_rules>
                1. **Perspective**: THIRD PERSON singular only (e.g., 'The candidate demonstrated...', 'I observed {candidate_name} performing...').
                2. **Tone**: Professional, authoritative, validating, and fact-based.
                3. **Volume**: Generate exactly 7 to 8 dense, technical paragraphs.
                4. **Inline Mapping**: Place the mapping inline, immediately after the sentence that demonstrates the criteria, rather than grouping them at the end of the paragraph. Do NOT repeat the Unit code within the same group if multiple criteria from that unit are met in that sentence.
                   Format: (UnitCode - LO#:PC #, #; LO#:PC #, #). Example: (ICT/CMR/005/L2 - LO1:PC 1.1, 1.2).
                5. **Exhaustive Usage**: You MUST integrate every single PC provided in the user list exactly once.
                6. **Narrative Flow**: Write a "continuous observation" story. Do not use bullet points in the main statement.
                7. **Focus**: Emphasize safe working practices, tool handling, and technical accuracy.
                8. **Technical Expansion**: DO NOT simply repeat the text of a Performance Criterion. Instead, expand upon it with specific, technically accurate details or examples that reflect what was observed. For example, instead of just saying "the candidate identified threats," describe the specific threats (e.g., DDOS, MAC spoofing) the candidate demonstrated knowledge of.
                </strict_rules>"""

                user_prompt = f"""
                Witness: {witness_name} ({witness_role})
                Candidate: {candidate_name}
                Date: {observation_date}
                Raw Notes: {witness_notes}
                Performance Criteria to cover: {", ".join(selected_pcs)}
                
                Generate a formal, dense witness statement incorporating all these details."""

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

    if 'current_witness_statement' in st.session_state:
        st.markdown("---")
        st.subheader("Preview & Finalize")
        st.write(st.session_state.current_witness_statement)
        
        col_save, col_word = st.columns(2)
        with col_save:
            if st.button("💾 Save to Database"):
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
                if success:
                    st.toast("Witness statement saved successfully!")
                    del st.session_state.current_witness_statement
                    st.rerun()
                else:
                    st.error(f"Error saving: {err}")
        
        with col_word:
            doc_bytes = export_witness_to_word(
                witness_name, witness_role, candidate_name, observation_date, 
                st.session_state.current_witness_statement, selected_pcs
            )
            st.download_button("📥 Download Word (.docx)", doc_bytes, f"Witness_{candidate_name}.docx")