from google import genai
from google.genai import types
import os
import json

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not found in environment variables.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Rewrite the following resume experience and skills to align with the target job description.
    Keep the tone professional and truthful based on the original data. Do not fabricate experience.
    
    Required Schema:
    {{
        "optimized_experience": "Rewritten experience and projects highlighting relevant keywords",
        "optimized_skills": "Comma separated list of skills, prioritizing those found in the job description"
    }}
    
    Original Experience: {parsed_data.get('experience', '')}
    Original Skills: {parsed_data.get('skills', '')}
    
    Target Job Description:
    {job_desc}
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
        raise RuntimeError(f"LLM optimization failed: {str(e)}")