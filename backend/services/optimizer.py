import google.generativeai as genai
import os

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not found in environment variables.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are an expert career coach and ATS optimization algorithm. 
    Rewrite the following resume experience and skills to perfectly align with the target job description.
    Keep the tone professional, action-oriented, and truthful based on the original data. Do not fabricate experience.
    
    Return ONLY a valid JSON object. Do not include markdown formatting or backticks.
    
    Required JSON Schema:
    {{
        "optimized_experience": "Rewritten experience and projects highlighting relevant keywords",
        "optimized_skills": "Comma separated list of skills, prioritizing those found in the job description"
    }}
    
    Original Experience: {parsed_data.get('experience', '')}
    Original Skills: {parsed_data.get('skills', '')}
    
    Target Job Description:
    {job_desc}
    """
    
    response = model.generate_content(prompt)
    
    import json
    import re
    try:
        cleaned_response = re.sub(r'^```json\s*|```\s*$', '', response.text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM output into structured JSON.")