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
        raise EnvironmentError("GROQ_API_KEY not found in environment variables.")
        
    client = Groq(api_key=api_key)
    
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
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert ATS parser. You must return ONLY a valid JSON object matching the requested schema. No conversational text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-8b-8192",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM output into structured JSON.")
    except Exception as e:
        print(f"GROQ API ERROR: {str(e)}")
        raise RuntimeError(f"LLM generation failed: {str(e)}")