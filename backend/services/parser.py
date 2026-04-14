import PyPDF2
from io import BytesIO
from groq import Groq
import os
import json

def extract_and_structure(file_storage):
    try:
        file_bytes = file_storage.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        raw_text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        return structure_with_llm(raw_text)
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {str(e)}")

def structure_with_llm(text):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY missing from .env")
        
    client = Groq(api_key=api_key)
    prompt = f"""
    You are an expert ATS Parser. Extract data into EXACT JSON schema. 
    If no Professional Summary exists, generate a 3-sentence ATS-friendly summary.
    
    Schema:
    {{
      "name": "Full Name",
      "email": "Email",
      "phone": "Phone",
      "linkedin": "LinkedIn URL",
      "summary": "Extracted or generated professional summary",
      "education": [{{"university": "", "city": "", "country": "", "degree": "", "grades": "", "start": "", "end": ""}}],
      "experience": [{{"company": "Company Name & Role", "description": "Bullet points", "start": "", "end": ""}}],
      "projects": [{{"name": "", "description": ""}}],
      "tech_skills": [{{"type": "Category", "skills": "Comma separated"}}],
      "soft_skills": ["List", "of", "soft", "skills"]
    }}
    
    Resume Text: {text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "Return ONLY valid JSON."}, {"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"Groq parsing failed: {str(e)}")