import PyPDF2
from io import BytesIO
import google.generativeai as genai
import os
import json
import re

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
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not found in environment variables.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are an ATS resume parser. Extract the following information from the provided text and return ONLY a valid JSON object. Do not include markdown formatting or backticks.
    
    Required JSON Schema:
    {{
        "name": "Full Name",
        "email": "Email Address",
        "education": "Education details (Degree, Institution, Year)",
        "experience": "Professional experience and projects",
        "skills": "Comma separated list of skills"
    }}
    
    Resume Text:
    {text}
    """
    
    response = model.generate_content(prompt)
    
    try:
        cleaned_response = re.sub(r'^```json\s*|```\s*$', '', response.text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM output into structured JSON.")