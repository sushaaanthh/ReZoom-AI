# Simple functional mock for the AI Matching Engine
def calculate_match(resume_text, job_desc):
    resume_words = set(resume_text.lower().split())
    job_words = set(job_desc.lower().split())
    
    # Exclude common stop words in a real app
    matched = list(resume_words.intersection(job_words))
    missing = list(job_words.difference(resume_words))
    
    score = (len(matched) / len(job_words)) * 100 if job_words else 0
    
    return {
        "score": round(score),
        "matched_keywords": matched[:10], # Top 10
        "missing_keywords": missing[:5],
        "suggestions": ["Add missing skills to your skills section", "Quantify your past experience"]
    }