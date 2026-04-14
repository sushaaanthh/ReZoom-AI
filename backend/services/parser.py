import PyPDF2
from io import BytesIO
from google import genai
from google.genai import types
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
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not found in environment variables.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Extract the following information from the provided text.
    
    Required Schema:
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
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM output into structured JSON.")
    except Exception as e:
        print(f"GEMINI API ERROR: {str(e)}") # Added for debugging
        raise RuntimeError(f"LLM generation failed: {str(e)}")