from groq import Groq
import os
import json

def calculate_match(resume_data, job_desc, filename):
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    
    # We force the LLM to output 'required_skills' so we have a mathematical baseline.
    prompt = f"""
    You are an Applicant Tracking System.
    1. Analyze the Job Description and list the core technical skills and tools required into "required_skills".
    2. Analyze the Resume Data.
    3. Cross-reference them. List the EXACT technical skills from the Job Description that are MISSING from the Resume Data into "missing_keywords". 
    Be brutal. If the resume does not explicitly state the skill, it is missing. Do not calculate a score.
    
    RETURN EXACT JSON NO MARKDOWN:
    {{
        "required_skills": ["skill1", "skill2", "skill3"],
        "missing_keywords": ["skill2"],
        "rule_violations": []
    }}
    
    Job Description: 
    {job_desc}
    
    Resume Data: 
    {resume_data}
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a JSON-only ATS extractor. No markdown."}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.0 
        )
        raw_content = completion.choices[0].message.content.strip()
        
        # Safe markdown stripping
        marker = "`" * 3
        if raw_content.startswith(marker + "json"):
            raw_content = raw_content[7:]
        if raw_content.endswith(marker):
            raw_content = raw_content[:-3]
            
        parsed_result = json.loads(raw_content.strip())
        
        # Extract the arrays
        required_kws = parsed_result.get("required_skills", [])
        missing = parsed_result.get("missing_keywords", [])
        violations = parsed_result.get("rule_violations", [])
        
        filename_lower = filename.lower()
        if any(word in filename_lower for word in ["cv", "resume", "2024", "2025", "2026", "2027"]):
            violations.append("Unprofessional filename (contains CV/Resume/Year)")
            
        # --- THE RUTHLESS MATH TRAP ---
        total_required = len(required_kws)
        if total_required == 0 or not job_desc or len(job_desc.strip()) < 5:
            # Fallback if no JD is provided or LLM fails to find skills
            return {
                "score": 10,
                "missing_keywords": ["Provide a detailed Target Job Description to analyze keywords."],
                "rule_violations": violations
            }
            
        missing_count = len(missing)
        
        # Calculate ratio of matched skills
        match_ratio = max(0, total_required - missing_count) / total_required
        
        # Exponential failure curve. (e.g. 50% match becomes 35% score)
        score = int((match_ratio ** 1.5) * 100)
        
        # Deduct 20 flat points for every rule violation
        score -= (len(violations) * 20)
        
        # Ensure score stays between 0 and 100
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "missing_keywords": missing,
            "rule_violations": violations
        }
        
    except Exception as e:
        raise RuntimeError(f"Groq matching failed: {str(e)}")