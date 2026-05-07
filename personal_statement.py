import streamlit as st
import datetime
import database as db
from ai_utils import validate_and_generate

@st.fragment
def render_nos_selection_for_student(nos_data):
    """
    Renders checkboxes for the student to select which PCs they want to include 
    in their personal statement.
    """
    local_selected_pcs = []
    
    unit_titles = list(nos_data.keys())
    tabs = st.tabs(unit_titles)
    
    for i, unit_key in enumerate(unit_titles):
        with tabs[i]:
            for lo_key, pcs in nos_data[unit_key].items():
                lo_id = lo_key.split(':')[0].replace("LO", "").strip()
                with st.expander(lo_key):
                    for pc in pcs:
                        if st.checkbox(pc, key=f"stmt_chk_{unit_key}_{pc}"):
                            unit_code = unit_key.split(':')[0]
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
    key = st.session_state.get('target_key')
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
    
    if st.button("Generate My Statement", type="primary"):
        if not reflection:
            st.error("Please provide some reflection notes first.")
        elif not selected_pcs:
            st.error("Please select at least one PC that you achieved.")
        else:
            with st.spinner("AI is crafting your professional narrative..."):
                # --- FIRST-PERSON AI PROMPT ---
                system_prompt = """You are a professional mentor helping a student draft their 'Personal Statement of Competence' for an NSQ Portfolio.
                Your task is to transform raw reflection notes into a professional narrative written strictly in the FIRST PERSON (using 'I', 'me', 'my').
                
                RULES:
                1. Tone: Professional, reflective, and confident.
                2. Perspective: First-person singular only.
                3. Integration: Weave the selected Performance Criteria (PCs) naturally into the story.
                4. Reference: Mention the PC code in parentheses, e.g., (PC 1.2), when describing the action that met it.
                5. Structure: Create a cohesive narrative, not a list. Explain the 'Why' and 'How' of the actions taken."""

                user_prompt = f"""
                Student Name: {student_name}
                Reflection Notes: {reflection}
                Performance Criteria to cover: {", ".join(selected_pcs)}
                
                Please write a 3-4 paragraph personal statement based on this information."""

                ai_statement = validate_and_generate(
                    provider=provider,
                    model_name=target_model,
                    api_key=key,
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )

                if "API_ERROR" in str(ai_statement):
                    st.error(ai_statement)
                else:
                    st.session_state.current_generated_statement = ai_statement

    # 4. Display Result and Save Logic
    if 'current_generated_statement' in st.session_state:
        st.markdown("---")
        st.subheader("Preview of Your Statement")
        st.write(st.session_state.current_generated_statement)
        
        if st.button("💾 Save to My Portfolio"):
            user_id = st.session_state.user_session.id
            success, err = db.insert_student_statement(
                user_id=user_id,
                student_name=student_name,
                trade_id=trade_id,
                unit_codes=", ".join(selected_pcs),
                reflection_notes=reflection,
                statement_text=st.session_state.current_generated_statement
            )
            if success:
                st.success("Statement saved successfully! You can view this in your portfolio history.")
            else:
                st.error(f"Failed to save: {err}")