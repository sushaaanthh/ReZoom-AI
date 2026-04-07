import PyPDF2

def extract_text(file_stream):
    """
    Extracts raw text from an uploaded PDF file stream.
    """
    extracted_text = ""
    try:
        # Read the PDF directly from the file stream
        pdf_reader = PyPDF2.PdfReader(file_stream)
        
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
                
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return None
        
    # Clean up excess whitespace
    return " ".join(extracted_text.split())