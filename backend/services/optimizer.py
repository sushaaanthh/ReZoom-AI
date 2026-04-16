from groq import Groq
import os
import json

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY missing")
        
    client = Groq(api_key=api_key)

    # REFINED PROMPT FOR RELEVANCE RANKING
    prompt_content = f"""
    You are an expert Resume Optimizer. Your task is to restructure the provided resume data to perfectly align with the target Job Description.

    CRITICAL INSTRUCTIONS:
    1. RELEVANCE RANKING: Reorder the 'tech_skills' so that categories and specific skills most relevant to the Job Description appear FIRST.
    2. KEYWORD INJECTION: Rewrite 'experience' descriptions to use action verbs and keywords found in the Job Description, while maintaining 100% truthfulness.
    3. SKILL PRIORITIZATION: Within each tech_skills category, list the most required technologies first.
    4. NO FABRICATION: Do not add skills the user does not have. Only re-prioritize and re-phrase.

    RETURN EXACT JSON FORMAT:
    {{
        "experience": [
            {{"company": "Company Name & Role", "start": "Date", "end": "Date", "description": "Bullet points optimized for relevance"}}
        ],
        "tech_skills": [
            {{"type": "Category Name", "skills": "Skill1, Skill2 (reordered by importance to JD)"}}
        ],
        "soft_skills": ["Skill 1", "Skill 2"]
    }}

    DATA TO PROCESS:
    Target Job: {job_desc}
    Original Experience: {parsed_data.get('experience', [])}
    Original Tech Skills: {parsed_data.get('tech_skills', [])}
    Original Soft Skills: {parsed_data.get('soft_skills', [])}
    """

    try:
        completion = client.chat.completions.create(
            # Added the 'user' role with our prompt_content
            messages=[
                {"role": "system", "content": "You are a professional resume parser that outputs ONLY valid JSON objects. Do not include markdown formatting or explanations."},
                {"role": "user", "content": prompt_content}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.2 # Lower temperature for more consistent, logical ranking
        )
        
        raw_content = completion.choices[0].message.content.strip()
        
        # Groq's json_object mode is usually clean, but we'll keep your safety check
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0]
            
        return json.loads(raw_content.strip())
        
    except Exception as e:
        raise RuntimeError(f"Groq optimization failed: {str(e)}")