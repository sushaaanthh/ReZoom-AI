from groq import Groq
import os
import json

def calculate_match(resume_data, job_desc, filename):
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    # RUTHLESS PROMPT: The AI only extracts, it does NOT calculate the score.
    prompt = f"""
    You are a strictly analytical Applicant Tracking System (ATS).
    
    Task:
    1. Read the Target Job Description. Identify the absolute most critical hard skills, tools, and technical requirements.
    2. Strictly cross-reference these EXACT terms with the Resume Data. 
    3. If a term from the Job Description is NOT explicitly mentioned in the Resume Data, add it to the "missing_keywords" array. Be ruthless.
    4. Check the filename: "{filename}". If it contains words like "CV", "Resume", or numbers (like years, e.g., 2024, 2026), add "Unprofessional filename formatting" to "rule_violations".
    5. DO NOT calculate a score. Just return the arrays.
    
    RETURN EXACT JSON FORMAT NO MARKDOWN:
    {{
        "missing_keywords": ["Exact Missing Skill 1", "Exact Missing Skill 2"],
        "rule_violations": ["Filename violation", "Missing bullet points"]
    }}
    
    Job Description: 
    {job_desc}
    
    Resume Data: 
    {resume_data}
    """
    
    try:
        # temperature=0.0 strips all "creativity" and leniency from the AI
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a JSON-only ATS text comparator. No markdown."}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.0 
        )
        raw_content = completion.choices[0].message.content.strip()
        
        # Safely stripping markdown without breaking the UI
        marker = "`" * 3
        if raw_content.startswith(marker + "json"):
            raw_content = raw_content[7:]
        if raw_content.endswith(marker):
            raw_content = raw_content[:-3]
            
        parsed_result = json.loads(raw_content.strip())
        
        missing = parsed_result.get("missing_keywords", [])
        violations = parsed_result.get("rule_violations", [])
        
        # --- PYTHON DOES THE MATH ---
        if not job_desc or len(job_desc.strip()) < 5:
            missing = ["Provide a Target Job Description to analyze keywords."]
            score = 40
        else:
            # Start at 100, deduct 10 for every missing skill, deduct 15 for every broken rule
            score = 100 - (len(missing) * 10) - (len(violations) * 15)
            
        # Floor the score at 0 so it doesn't go into negative numbers
        score = max(0, min(100, score))
        
        # Re-pack the JSON with the mathematically perfect score
        return {
            "score": score,
            "missing_keywords": missing,
            "rule_violations": violations
        }
        
    except Exception as e:
        raise RuntimeError(f"Groq matching failed: {str(e)}")