from groq import Groq
import os
import json

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY missing.")
        
    client = Groq(api_key=api_key)
    prompt = f"""
    Rewrite experience and skills to align with the job description. Do not fabricate. Return ONLY valid JSON.
    Schema: {{"optimized_experience": "Rewritten experience", "optimized_skills": "Comma separated skills"}}
    Original Experience: {parsed_data.get('experience', '')}
    Original Skills: {parsed_data.get('skills', '')}
    Target Job: {job_desc}
    """
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only career coach. No markdown, no conversational text."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise RuntimeError(f"LLM optimization failed: {str(e)}")