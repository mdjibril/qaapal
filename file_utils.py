from docx import Document
from docx.shared import Pt
from io import BytesIO

def export_to_word(name, date, report_text, assessor_name, assessor_id, timeline="N/A", atmosphere="N/A", selected_pcs=None):
    """
    Generates a standardized NSQ Word report.
    """
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)
    header = doc.add_heading('National Skills Qualification (NSQ) - Assessment Report', 0)
    header.alignment = 1 
    table = doc.add_table(rows=3, cols=2)
    table.style = 'Table Grid'
    table.rows[0].cells[0].text = f"Candidate Name: {name}"
    table.rows[0].cells[1].text = f"Date: {date}"
    table.rows[1].cells[0].text = f"Timeline: {timeline}"
    table.rows[1].cells[1].text = f"Assessor: {assessor_name}"
    table.rows[2].cells[0].text = f"Atmosphere: {atmosphere}"
    table.rows[2].cells[1].text = "Status: Competent (Progressing)"
    doc.add_paragraph("\n")
    doc.add_heading('Observation Narrative & Evidence', level=1)
    doc.add_paragraph(report_text)
    doc.add_paragraph("\n")
    doc.add_heading('Mapped Performance Criteria Summary', level=2)
    
    if selected_pcs and isinstance(selected_pcs, list):
        units_dict = {}
        for pc_str in selected_pcs:
            parts = pc_str.split(' - ')
            if len(parts) >= 3:
                unit = parts[0].strip()
                lo_num = parts[1].strip()
                lo = f"LO {lo_num}"
                criterion = parts[2].split(':')[0].strip()
                units_dict.setdefault(unit, {}).setdefault(lo, []).append(criterion)

        for unit, lo_map in units_dict.items():
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{unit}: ").bold = True
            lo_parts = [f"{lo}:{', '.join(pcs)}" for lo, pcs in lo_map.items()]
            p.add_run("; ".join(lo_parts))
    elif selected_pcs and isinstance(selected_pcs, str):
        # If it's a comma-separated string of unit codes (from history)
        p = doc.add_paragraph(style='List Bullet')
        p.add_run("Units Covered: ").bold = True
        p.add_run(selected_pcs)

    doc.add_paragraph("\n")
    doc.add_heading(f'Assessor Signature: _______________________', level=3)
    doc.add_paragraph(f"Verified by {assessor_name} ({assessor_id}) on {date}")
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()