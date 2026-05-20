from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from io import BytesIO
import re

def set_cell_border(cell, **kwargs):
    """
    Utility to set specific cell borders using XML.
    Example: set_cell_border(cell, top={"val": "nil"}, bottom={"val": "nil"})
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn('w:tcBorders'))
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('start', 'top', 'end', 'bottom', 'left', 'right'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key in ["val", "color", "sz", "space", "shadow"]:
                if key in edge_data:
                    element.set(qn('w:{}'.format(key)), str(edge_data[key]))

def get_unit_number(unit_code):
    """Extracts the numeric part of a unit code (e.g., ICT/SMC/008/L2 -> 8)."""
    try:
        parts = unit_code.split('/')
        if len(parts) >= 3:
            # Convert to int then back to string to remove leading zeros (e.g., '008' -> '8')
            return str(int(parts[2]))
        return unit_code.strip()
    except (ValueError, IndexError):
        return unit_code.strip()

def extract_mapping(text):
    """Parses a paragraph to separate narrative from the technical PC mapping block."""
    # Find all parenthesized blocks in the text
    all_parenthesized_blocks = list(re.finditer(r'\((.*?)\)', text))
    
    mapping_match = None
    if all_parenthesized_blocks:
        # Iterate backwards to find the last parenthesized block that looks like a mapping
        for match in reversed(all_parenthesized_blocks):
            inner_content = match.group(1) # Content inside parentheses
            # Check if it contains a unit code pattern and 'LO'
            if re.search(r'^[A-Z0-9/]+\s*-\s*LO', inner_content):
                mapping_match = match
                break
    
    if not mapping_match:
        return "", "", text
    
    inner_content = mapping_match.group(1) # Content inside the parentheses
    
    # Split the inner content by semicolon, but only if a new Unit Code follows.
    # We use a 'lookahead' to check for a unit code pattern (caps/numbers/slashes followed by a dash).
    segments = re.split(r';\s*(?=[A-Z0-9/]+\s*-)', inner_content)
    
    unit_nums = []
    mapping_parts = []

    for segment in segments:
        if '-' in segment:
            # Separate the Unit part from the LO mapping part
            u_code, mapping = segment.split('-', 1)
            unit_nums.append(get_unit_number(u_code.strip()))
            mapping_parts.append(mapping.strip())
        else:
            # Fallback for LOs that might still belong to the previous unit segment,
            # or if the segment doesn't contain a dash (e.g., just "PC 1.1")
            mapping_parts.append(segment.strip())
            
    # Remove duplicates and join
    final_units = ", ".join(dict.fromkeys(unit_nums))
    final_mapping = "; ".join(mapping_parts)
    
    # Narrative is the original paragraph text without the full matched block (including parentheses)
    narrative = text.replace(mapping_match.group(0), "").strip()
    
    # Clean up any trailing punctuation left by removing the mapping block
    narrative = re.sub(r'\s*[.,;:]+$', '', narrative).strip()

    return final_units, final_mapping, narrative

def _create_official_nsq_template(doc, candidate_name, date, report_text, units_summary, criteria_summary, evidence_type="observation", witness_name=None, witness_role=None):
    """
    Internal helper to generate the official CPN-ARF-02 Performance Evidence Record Form.
    """
    # Global Style Adjustments
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Set Page Margins to 0.75"
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    # --- HEADER SECTION (Table 1) ---
    header_table = doc.add_table(rows=1, cols=2)
    header_table.width = Inches(7.0)
    header_table.style = 'Table Grid'
    header_table.cell(0, 0).text = "[LOGO]"
    header_table.cell(0, 1).text = "R.EF: CPN-ARF-02, Performance Evidence Record Form."
    header_table.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # --- UNDERLINED TITLE ---
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("\nASSESSORS AND CANDIDATES PERFORMANCE EVIDENCE RECORD FORM")
    run.bold = True
    run.underline = True
    run.size = Pt(12)

    # --- USER METADATA (Table 2) ---
    meta_table = doc.add_table(rows=1, cols=2)
    meta_table.style = 'Table Grid'
    meta_table.width = Inches(7.0)
    meta_table.cell(0, 0).text = f"Candidate Name: {candidate_name}"
    meta_table.cell(0, 1).text = f"Units: {units_summary}"

    # --- INSTRUCTION BLOCK ---
    instr = doc.add_paragraph("\nThis form can be used for Assessor’s observation of practical workplace activities or Candidates statement of practical activities. NB: Assessor may wish to ask a candidate some questions relating to the activity and record the question and the answer in this form also.")
    instr.italic = True
    instr.paragraph_format.space_after = Pt(10)

    # Clean report text: Remove summary block and split into paragraphs
    clean_report = report_text.split("----- SUMMARY OF CRITERIA COVERED -----")[0].strip()

    # Group detached mapping blocks with their parent paragraphs to ensure row alignment
    raw_lines = [line.strip() for line in clean_report.splitlines() if line.strip()]
    paragraphs = []
    for line in raw_lines:
        if line.startswith("(") and " - LO" in line and paragraphs:
            paragraphs[-1] = f"{paragraphs[-1]} {line}"
        else:
            paragraphs.append(line)

    # --- MAIN ACTIVITY GRID (Table 3) ---
    # We create a table with 3 header rows + one row for every paragraph
    num_data_rows = max(1, len(paragraphs))
    main_table = doc.add_table(rows=3 + num_data_rows, cols=5)
    main_table.style = 'Table Grid'
    main_table.autofit = False
    main_table.width = Inches(7.0)

    # Force fixed table layout at XML level to ensure widths are strictly respected
    tbl = main_table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    tblLayout = tblPr.find(qn('w:tblLayout'))
    if tblLayout is None:
        tblLayout = OxmlElement('w:tblLayout')
        tblPr.append(tblLayout)
    tblLayout.set(qn('w:type'), 'fixed')

    # Set column widths (Unit: 0.58, LO: 1.50, Sub-columns: 1.64 each)
    # Total width sums to exactly 7.0" to fit perfectly within 0.75" margins
    col_widths = [0.58, 1.50, 1.64, 1.64, 1.64]
    for i, width in enumerate(col_widths):
        main_table.columns[i].width = Inches(width)
        for cell in main_table.columns[i].cells:
            cell.width = Inches(width)

    # Header Row 1: Merging for "Tick which evidence method"
    main_table.cell(0, 0).text = "Unit"
    main_table.cell(0, 1).text = "LO/Assessment criteria"
    tick_header = main_table.cell(0, 2).merge(main_table.cell(0, 4))
    tick_header.text = "Tick which evidence method"
    tick_header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Header Row 2 & 3: Merging Unit and LO vertically across header rows
    main_table.cell(0, 0).merge(main_table.cell(2, 0))
    main_table.cell(0, 1).merge(main_table.cell(2, 1))

    # Evidence Checkboxes
    check_obs = "☑" if evidence_type == "observation" else "☐"
    check_wit = "☑" if evidence_type == "witness" else "☐"
    check_per = "☑" if evidence_type == "personal" else "☐"
    
    main_table.cell(1, 2).text = f"{check_obs} Observation"
    main_table.cell(1, 3).text = f"{check_wit} Witness statement"
    main_table.cell(1, 4).text = f"{check_per} Personal statement"

    # Record Label
    record_label = main_table.cell(2, 2).merge(main_table.cell(2, 4))
    record_label.text = "Record of observed activity and performance."
    record_label.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- DATA ROWS ---
    if not paragraphs:
        row = main_table.rows[3]
        row.cells[0].text = units_summary
        row.cells[1].text = criteria_summary
        row.cells[2].merge(row.cells[4]).text = clean_report
    else:
        for i, p_text in enumerate(paragraphs):
            u_num, mapping, narrative = extract_mapping(p_text)
            row = main_table.rows[3 + i]
            
            row.cells[0].text = u_num
            row.cells[1].text = mapping
            
            # Merge the narrative cells and insert text
            content_cell = row.cells[2].merge(row.cells[4])
            content_cell.text = narrative

            # Add space after each paragraph to create a clear separation between entries
            row.cells[0].paragraphs[0].paragraph_format.space_after = Pt(12)
            row.cells[1].paragraphs[0].paragraph_format.space_after = Pt(12)
            content_cell.paragraphs[0].paragraph_format.space_after = Pt(12)

            # Adjust borders to make multiple rows look like one continuous box
            # We remove the internal horizontal lines between paragraphs
            if len(paragraphs) > 1:
                # If not the last paragraph, remove bottom border
                if i < len(paragraphs) - 1:
                    for cell in row.cells:
                        set_cell_border(cell, bottom={"val": "nil"})
                # If not the first paragraph, remove top border
                if i > 0:
                    for cell in row.cells:
                        set_cell_border(cell, top={"val": "nil"})

    # Apply top vertical alignment to all data rows
    for row in main_table.rows[3:]:
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # --- DECLARATION ---
    doc.add_paragraph("\nI confirm that the evidence listed above is true record of the perfumed activities observed during this assessment.")

    # --- SIGNATURES GRID (Table 4) ---
    sig_table = doc.add_table(rows=4, cols=2)
    sig_table.style = 'Table Grid'
    
    sigs = [
        "Work base Assessor / witness Signature:",
        "Candidate's Signature:",
        "Assessor's Signature:",
        "Internal Verifier's Signature:"
    ]
    
    for i, label in enumerate(sigs):
        sig_table.cell(i, 0).text = f"{label} __________________"
        sig_table.cell(i, 1).text = f"Date: {date}"

def export_to_word(name, date, report_text, assessor_name, assessor_id, timeline="N/A", atmosphere="N/A", selected_pcs=None):
    """
    Generates a standardized NSQ Word report.
    """
    doc = Document()
    
    units_list = []
    criteria_list = []

    if selected_pcs and isinstance(selected_pcs, list):
        for pc_str in selected_pcs:
            parts = pc_str.split(' - ')
            if len(parts) >= 3:
                units_list.append(parts[0].strip())
                criteria_list.append(f"LO{parts[1]}:{parts[2].split(':')[0]}")
    elif isinstance(selected_pcs, str) and selected_pcs:
        units_list = [u.strip() for u in selected_pcs.split(',') if u.strip()]

    units_summary = ", ".join(dict.fromkeys([get_unit_number(u) for u in units_list]))
    criteria_summary = "; ".join(criteria_list)

    _create_official_nsq_template(
        doc=doc,
        candidate_name=name,
        date=date,
        report_text=report_text,
        units_summary=units_summary,
        criteria_summary=criteria_summary,
        evidence_type="observation"
    )
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_witness_to_word(witness_name, witness_role, candidate_name, date, statement_text, selected_pcs=None):
    """
    Generates a standardized NSQ Witness Statement Word document.
    """
    doc = Document()
    
    units_list = []
    criteria_list = []

    if selected_pcs and isinstance(selected_pcs, list):
        for pc_str in selected_pcs:
            parts = pc_str.split(' - ')
            if len(parts) >= 3:
                units_list.append(parts[0].strip())
                criteria_list.append(f"LO{parts[1]}:{parts[2].split(':')[0]}")
    else:
        if isinstance(selected_pcs, str) and selected_pcs:
            units_list = [u.strip() for u in selected_pcs.split(',') if u.strip()]
        criteria_list = ["Refer to narrative"]

    units_summary = ", ".join(dict.fromkeys([get_unit_number(u) for u in units_list]))
    criteria_summary = "; ".join(criteria_list)

    _create_official_nsq_template(
        doc=doc,
        candidate_name=candidate_name,
        date=date,
        report_text=statement_text,
        units_summary=units_summary,
        criteria_summary=criteria_summary,
        evidence_type="witness",
        witness_name=witness_name,
        witness_role=witness_role
    )

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_personal_statement_to_word(name, date, statement_text, selected_pcs=None):
    """
    Generates a standardized NSQ Personal Statement Word document.
    """
    doc = Document()
    
    units_list = []
    criteria_list = []

    if selected_pcs and isinstance(selected_pcs, list):
        for pc_str in selected_pcs:
            parts = pc_str.split(' - ')
            if len(parts) >= 3:
                units_list.append(parts[0].strip())
                criteria_list.append(f"LO{parts[1]}:{parts[2].split(':')[0]}")
    else:
        if isinstance(selected_pcs, str) and selected_pcs:
            units_list = [u.strip() for u in selected_pcs.split(',') if u.strip()]
        criteria_list = ["Refer to narrative"]

    units_summary = ", ".join(dict.fromkeys([get_unit_number(u) for u in units_list]))
    criteria_summary = "; ".join(criteria_list)

    _create_official_nsq_template(
        doc=doc,
        candidate_name=name,
        date=date,
        report_text=statement_text,
        units_summary=units_summary,
        criteria_summary=criteria_summary,
        evidence_type="personal"
    )

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()