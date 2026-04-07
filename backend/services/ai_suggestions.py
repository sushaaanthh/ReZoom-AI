import re

def generate_suggestions(resume_text, job_desc):
    """
    Analyzes resume text against a job description to provide actionable improvements.
    """
    suggestions = {
        "missing_skills": [],
        "phrasing_improvements": [],
        "general_tips": []
    }
    
    resume_lower = resume_text.lower()
    job_lower = job_desc.lower()
    
    # 1. Detect Missing Core Tech/Skills
    # In a real app, this list would be massive or powered by an LLM
    tech_keywords = [
        "python", "javascript", "react", "node.js", "sql", "nosql", 
        "docker", "aws", "git", "agile", "machine learning", "html", "css"
    ]
    
    for tech in tech_keywords:
        if tech in job_lower and tech not in resume_lower:
            suggestions["missing_skills"].append(tech.title())

    # 2. Phrasing & Action Verbs Check
    weak_phrases = ["responsible for", "helped with", "worked on", "duties included"]
    for phrase in weak_phrases:
        if phrase in resume_lower:
            suggestions["phrasing_improvements"].append(
                f"Replace '{phrase}' with strong action verbs like 'Spearheaded', 'Engineered', or 'Managed'."
            )

    # 3. Quantifiable Metrics Check
    # Regex to check if there are any numbers/percentages in the text
    has_metrics = bool(re.search(r'\d+%?|\b(one|two|three|four|five|six|seven|eight|nine|ten)\b', resume_lower))
    if not has_metrics:
        suggestions["general_tips"].append(
            "Your resume lacks quantifiable metrics. Try adding numbers to your achievements (e.g., 'Increased performance by 20%')."
        )
        
    return suggestions