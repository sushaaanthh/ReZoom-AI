from groq import Groq
import os
import json

def optimize_resume_content(parsed_data, job_desc):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY missing")
        
    client = Groq(api_key=api_key)

    prompt_content = f"""
You are an AI Resume Optimization Agent.

Your job is NOT just rewriting. You must ANALYZE, SCORE, RANK, and then RESTRUCTURE.

---

### STEP 1: EXTRACT JD SIGNAL
- Extract top 10–15 IMPORTANT keywords from the Job Description.
- Prioritize: tools, frameworks, languages, role focus (e.g., backend, frontend, data).

---

### STEP 2: SCORE RESUME ELEMENTS
For EACH:
- tech_skills category
- individual skill inside category
- experience bullet / description

Assign a relevance score from 0 to 1 based on match with JD keywords.

---

### STEP 3: REORDER (CRITICAL)
- Sort tech_skills categories by HIGHEST scoring skills inside them
- Sort skills within each category by score (descending)
- Sort experience entries by relevance
- Within each experience.description:
    - Rewrite bullets to emphasize JD keywords
    - Most relevant bullet FIRST

---
r-
### STEP 4: CONTEXTUAL REWRITING RULES
- Use strong action verbs (Built, Developed, Optimized, Designed)
- Map existing work to JD keywords IF logically valid
- DO NOT fabricate tools, projects, or responsibilities
- DO NOT introduce new companies or roles

---

### HARD CONSTRAINTS (VERY IMPORTANT)
- ZERO hallucination
- DO NOT add new skills
- DO NOT infer unmentioned technologies
- Only reorder + rephrase existing data

---

### OUTPUT FORMAT (STRICT JSON ONLY)

Return ONLY this structure:

{{
    "experience": [
        {{
            "company": "Company Name & Role",
            "start": "Date",
            "end": "Date",
            "description": "Rewritten bullet points ordered by relevance"
        }}
    ],
    "tech_skills": [
        {{
            "type": "Category Name",
            "skills": "Skill1, Skill2, Skill3"
        }}
    ],
    "soft_skills": ["Skill 1", "Skill 2"]
}}

---

### VALIDATION BEFORE OUTPUT
- Ensure JSON is valid
- Ensure no extra keys
- Ensure no missing fields
- Ensure ordering reflects relevance scoring

---

### INPUT DATA

JOB DESCRIPTION:
{job_desc}

RESUME DATA:
Experience: {parsed_data.get('experience', [])}
Tech Skills: {parsed_data.get('tech_skills', [])}
Soft Skills: {parsed_data.get('soft_skills', [])}
"""

    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON generator. Output ONLY valid JSON. No explanations."
                },
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.1  # Lower = more deterministic ranking
        )

        raw_content = completion.choices[0].message.content.strip()

        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0]

        return json.loads(raw_content.strip())

    except Exception as e:
        raise RuntimeError(f"Groq optimization failed: {str(e)}")