import PyPDF2

def parse_resume(file):
    text = ""

    try:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    except:
        return {"error": "Failed to read PDF"}

    return {
        "text": text,
        "length": len(text)
    }