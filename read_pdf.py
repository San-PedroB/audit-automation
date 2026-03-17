import pdfplumber

pdf_path = "Auditorias_Clientes/Casino Talca/11-03/Informe Crystal.docx.pdf"
output_path = "pdf_output.txt"

with pdfplumber.open(pdf_path) as pdf, open(output_path, "w", encoding="utf-8") as out:
    out.write(f"Total páginas: {len(pdf.pages)}\n")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        out.write(f"\n===== PÁGINA {i+1} =====\n")
        out.write(text if text else "[Sin texto extraíble en esta página]")
        out.write("\n")

print("Listo! Texto extraído en pdf_output.txt")
