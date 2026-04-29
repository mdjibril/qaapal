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
        for pc in selected_pcs:
            parts = pc.split(' - ')
            if len(parts) >= 2:
                unit, criterion = parts[0], parts[1].split(':')[0]
                units_dict.setdefault(unit, []).append(criterion)
        for unit, pcs in units_dict.items():
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{unit}: ").bold = True
            p.add_run(", ".join(pcs))
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