import PyPDF2
from io import BytesIO
from groq import Groq
import os
import json

def extract_and_structure(file_storage):
    try:
        file_bytes = file_storage.read()
        pdf_file = BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        raw_text = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                raw_text.append(text)
                
        if not raw_text:
            raise ValueError("No readable text found in PDF.")
            
        full_text = " ".join(" ".join(raw_text).split())
        
        return structure_with_llm(full_text)
        
    except Exception as e:
        raise RuntimeError(f"Parsing failed: {str(e)}")

def structure_with_llm(text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY missing.")
        
    client = Groq(api_key=api_key)
    prompt = f"""
    Extract the following information. Return ONLY valid JSON.
    Schema: {{"name": "Full Name", "email": "Email Address", "education": "Education details", "experience": "Professional experience", "skills": "Comma separated skills"}}
    Text: {text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only ATS parser. No markdown, no conversational text."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"LLM parsing failed: {str(e)}")