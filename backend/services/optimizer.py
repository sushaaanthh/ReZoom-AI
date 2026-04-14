from groq import Groq
import os
import json

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not found in environment variables.")
        
    client = Groq(api_key=api_key)
    
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
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert career coach and ATS optimization algorithm. You must return ONLY a valid JSON object. No conversational text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM output into structured JSON.")
    except Exception as e:
        print(f"GROQ API ERROR: {str(e)}")
        raise RuntimeError(f"LLM optimization failed: {str(e)}")