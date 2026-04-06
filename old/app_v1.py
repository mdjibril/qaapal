import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(page_title="NSQ Report Architect", layout="wide")

# Securely input API Key
api_key = st.sidebar.text_input("AIzaSyBqxd-ricU_Mp--Un3e2l5GpNRI5-mFg88", type="password")

# if api_key:
    # genai.configure(api_key=api_key)
    # model = genai.GenerativeModel('gemini-1.5-flash')
    # model = genai.GenerativeModel('models/gemini-1.5-flash')
    # model = genai.GenerativeModel('gemini-pro')

if api_key:
    genai.configure(api_key=api_key)
    
    # 1. Let's find out exactly what models are available to your key
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 2. Pick the correct one. We'll try the full path first.
    # On many systems, it must be 'models/gemini-1.5-flash-latest' or 'models/gemini-1.5-flash'
    target_model = 'models/gemini-1.5-flash' 
    
    if target_model not in available_models:
        # Fallback to the first available flash model if the name is slightly different
        flash_models = [m for m in available_models if 'flash' in m]
        target_model = flash_models[0] if flash_models else available_models[0]

    model = genai.GenerativeModel(target_model)
    st.sidebar.success(f"Connected to: {target_model}")

# --- DATA STRUCTURE (The NOS Engine) ---
# In the Enterprise version, this will come from a Database
NOS_DATA = {
    "Unit 4: Hardware Identification": [
        "PC 1.1: Identify internal components (CPU, RAM, Motherboard)",
        "PC 2.1: Use appropriate tools for disassembly",
        "PC 3.3: Identify legacy vs modern expansion slots"
    ],
    "Unit 5: Installation & Integration": [
        "PC 1.1: Install CPU and thermal assembly",
        "PC 2.2: Connect storage devices (SATA/NVMe)",
        "PC 4.1: Verify system boot in BIOS/UEFI"
    ]
}

# --- UI DESIGN ---
st.title("📝 NSQ Report Generator")
st.subheader("Assessor Tool for ICT Level 3")

with st.expander("Student & Session Info", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Candidate Name")
        assessment_date = st.date_input("Assessment Date")
    with col2:
        time_frame = st.text_input("Timeline (e.g., 9:10AM – 2:10PM)")
        atmosphere = st.text_area("Atmospheric Details", "The lab temperature was moderate as the fan was cooling it")

st.markdown("### Select Achieved Performance Criteria (PCs)")
selected_pcs = []

# Generate Checkboxes dynamically from our NOS_DATA
tabs = st.tabs(list(NOS_DATA.keys()))
for i, unit in enumerate(NOS_DATA.keys()):
    with tabs[i]:
        for pc in NOS_DATA[unit]:
            if st.checkbox(pc, key=f"{unit}_{pc}"):
                selected_pcs.append(pc)

learning_moment = st.text_area("Learning Moment / Hook", "Describe a specific struggle or breakthrough...")

# --- GENERATION LOGIC ---
if st.button("Generate Narrative Report"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    else:
        with st.spinner("AI is crafting the report according to NOS standards..."):
            prompt = f"""
            You are a professional NSQ Assessor. Write a formal 10-paragraph narrative report for {student_name}.
            
            CONTEXT:
            - Timeline: {time_frame}
            - Atmosphere: {atmosphere}
            - Achieved PCs: {', '.join(selected_pcs)}
            - Observation: {learning_moment}
            
            REQUIREMENTS:
            1. Use professional technical language relevant to ICT Computer Hardware Level 3.
            2. Map the relevant PCs to the end of each paragraph in brackets (e.g., Unit 4: PC 1.1).
            3. Ensure the report flows chronologically.
            4. Tone: Objective, supportive, and formal.
            """
            
            response = model.generate_content(prompt)
            report_text = response.text
            
            st.markdown("---")
            st.markdown("### Generated Report Preview")
            st.write(report_text)
            
            # Simple Download Button (Text format for now)
            st.download_button("Download Report as TXT", report_text, file_name=f"{student_name}_Report.txt")