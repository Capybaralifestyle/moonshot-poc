from fpdf import FPDF


def export_text_to_pdf(text: str, file_path: str) -> None:
    """Export plain text to a simple PDF file."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        pdf.multi_cell(0, 10, line)
    pdf.output(file_path)
