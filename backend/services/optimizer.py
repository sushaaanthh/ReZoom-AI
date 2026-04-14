from groq import Groq
import os
import json

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY missing")
        
    client = Groq(api_key=api_key)
    prompt = f"""
    Rewrite experience and skills to align with the job description. Do not fabricate.
    Keep technical skills and soft skills SEPARATE.
    
    RETURN EXACT JSON FORMAT NO MARKDOWN:
    {{
        "experience": [
            {{"company": "Company Name & Role", "start": "Date", "end": "Date", "description": "Rewritten bullet points matching JD keywords"}}
        ],
        "tech_skills": [
            {{"type": "Category", "skills": "Rewritten comma separated skills"}}
        ],
        "soft_skills": ["Soft skill 1", "Soft skill 2"]
    }}
    
    Original Experience: {parsed_data.get('experience', [])}
    Original Tech Skills: {parsed_data.get('tech_skills', [])}
    Original Soft Skills: {parsed_data.get('soft_skills', [])}
    Target Job: {job_desc}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "Return ONLY valid JSON. No markdown."}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        raw_content = completion.choices[0].message.content.strip()
        
        # Safely stripping markdown without breaking the UI's copy button
        marker = "`" * 3
        if raw_content.startswith(marker + "json"):
            raw_content = raw_content[7:]
        if raw_content.endswith(marker):
            raw_content = raw_content[:-3]
            
        return json.loads(raw_content.strip())
    except Exception as e:
        raise RuntimeError(f"Groq optimization failed: {str(e)}")