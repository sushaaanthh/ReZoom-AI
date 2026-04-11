import re

def calculate_match(resume_text, job_desc):
    if not resume_text or not job_desc:
        return {"score": 0, "matched_keywords": [], "missing_keywords": []}
        
    resume_lower = resume_text.lower()
    
    raw_job_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', job_desc.lower()))
    stop_words = {
        "and", "the", "for", "with", "you", "are", "this", "that", 
        "from", "have", "what", "will", "can", "your", "our", "team",
        "their", "they", "but", "not"
    }
    job_keywords = raw_job_words - stop_words
    
    if not job_keywords:
        return {"score": 0, "matched_keywords": [], "missing_keywords": []}
        
    matched = []
    missing = []
    
    for kw in job_keywords:
        if kw in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)
            
    match_ratio = len(matched) / len(job_keywords)
    
    baseline_padding = min(20, len(resume_lower) / 500)
    final_score = min(100, (match_ratio * 100) + baseline_padding)
    
    return {
        "score": int(final_score),
        "matched_keywords": matched[:10],
        "missing_keywords": missing[:8]
    }