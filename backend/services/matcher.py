from groq import Groq
import os
import json
import re


# ---------------------------------------------------------
# HELPER: Safe JSON parse
# ---------------------------------------------------------
def safe_parse_resume(resume_data):
    if isinstance(resume_data, dict):
        return resume_data
    if isinstance(resume_data, str):
        try:
            return json.loads(resume_data)
        except Exception:
            return {}
    return {}


# ---------------------------------------------------------
# HELPER: Normalize text
# ---------------------------------------------------------
def normalize_text(data):
    try:
        return json.dumps(data).lower()
    except Exception:
        return ""


# ---------------------------------------------------------
# HELPER: Robust exact match (handles C++, C#, .NET)
# ---------------------------------------------------------
def is_exact_match(term, text):
    term = term.lower().strip()
    if not term:
        return False

    escaped = re.escape(term)
    pattern = r'(?<![a-z0-9])' + escaped + r'(?![a-z0-9])'
    return re.search(pattern, text) is not None


# ---------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------
def calculate_match(resume_data, job_desc, filename):

    resume_data = safe_parse_resume(resume_data)

    # ---------------------------------------------------------
    # FAILSAFE: Invalid JD
    # ---------------------------------------------------------
    if not job_desc or len(job_desc.strip()) < 15:
        return {
            "score": 10,
            "missing_keywords": ["Invalid or empty Job Description"],
            "rule_violations": ["ATS scan requires a valid Job Description"]
        }

    # ---------------------------------------------------------
    # GROQ CLIENT
    # ---------------------------------------------------------
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # ---------------------------------------------------------
    # STEP 1: JD EXTRACTION (LLM ONLY)
    # ---------------------------------------------------------
    prompt = f"""
You are a strict JSON extractor.

Extract ONLY from the Job Description.

Return EXACT JSON:
{{
    "jd_req_years": int,
    "jd_keywords": ["..."],
    "jd_skills": ["..."]
}}

Rules:
- jd_req_years = minimum years (0 if not mentioned)
- jd_keywords = max 10 domain concepts
- jd_skills = max 15 hard technical skills
- DO NOT hallucinate
- DO NOT return empty arrays unless absolutely nothing exists

Job Description:
{job_desc}
"""

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(completion.choices[0].message.content)

    except Exception as e:
        raise RuntimeError(f"Groq extraction failed: {str(e)}")

    # ---------------------------------------------------------
    # SAFE EXTRACTION (NO FREE PASSES)
    # ---------------------------------------------------------
    req_years = parsed.get("jd_req_years", 0)

    jd_kws = parsed.get("jd_keywords") or []
    jd_skills = parsed.get("jd_skills") or []

    # HARD LIMITS
    jd_kws = jd_kws[:10]
    jd_skills = jd_skills[:15]

    # ---------------------------------------------------------
    # PREPARE RESUME TEXT
    # ---------------------------------------------------------
    resume_text = normalize_text(resume_data)

    # ---------------------------------------------------------
    # STEP 2: FORMATTING CHECK (15%)
    # ---------------------------------------------------------
    score = 0.0
    violations = []
    missing = []

    fmt_score = 15.0

    has_edu = bool(resume_data.get("education"))
    has_exp = bool(resume_data.get("experience"))
    has_skills = bool(resume_data.get("tech_skills"))

    if not has_edu:
        fmt_score -= 5
        violations.append("Missing Education section")

    if not has_exp:
        fmt_score -= 5
        violations.append("Missing Experience section")

    if not has_skills:
        fmt_score -= 5
        violations.append("Missing Skills section")

    score += max(0, fmt_score)

    # ---------------------------------------------------------
    # STEP 3: KEYWORD MATCHING (35%)
    # ---------------------------------------------------------
    keyword_score = 0.0
    matched_kws = []

    if len(jd_kws) == 0:
        # IMPORTANT: DO NOT GIVE FULL MARKS
        keyword_score = 5.0
        violations.append("JD extraction weak: no keywords found")
    else:
        for kw in jd_kws:
            if is_exact_match(kw, resume_text):
                matched_kws.append(kw)
            else:
                missing.append(kw)

        keyword_score = (len(matched_kws) / len(jd_kws)) * 35.0

    score += keyword_score

    # ---------------------------------------------------------
    # STEP 4: SKILL MATCHING (30%)
    # ---------------------------------------------------------
    skill_score = 0.0
    matched_skills = []

    if len(jd_skills) == 0:
        # NO FREE PASS
        skill_score = 5.0
        violations.append("JD extraction weak: no skills found")
    else:
        for sk in jd_skills:
            if is_exact_match(sk, resume_text):
                matched_skills.append(sk)
            else:
                missing.append(sk)

        skill_score = (len(matched_skills) / len(jd_skills)) * 30.0

    score += skill_score

    # ---------------------------------------------------------
    # STEP 5: EXPERIENCE ANALYSIS (20%)
    # ---------------------------------------------------------
    exp_score = 0.0

    experience_entries = resume_data.get("experience", [])

    # crude estimation
    actual_years = len(experience_entries) * 1.5

    if req_years > 0:
        if actual_years >= req_years:
            exp_score = 20.0
        else:
            ratio = actual_years / req_years
            exp_score = max(0, ratio * 10.0)  # heavy penalty

            violations.append(
                f"Experience deficit: required {req_years} yrs, found ~{int(actual_years)} yrs"
            )
    else:
        exp_score = 15.0  # not full marks

    score += exp_score

    # ---------------------------------------------------------
    # STEP 6: HARD FAIL RULES
    # ---------------------------------------------------------
    total_required = len(jd_kws) + len(jd_skills)
    total_matched = len(matched_kws) + len(matched_skills)

    # 🚨 Nuke rule
    if total_required >= 5 and total_matched == 0:
        return {
            "score": 12,
            "missing_keywords": jd_kws + jd_skills,
            "rule_violations": [
                "Resume is completely irrelevant to job requirements"
            ]
        }

    # 🚨 No tech skills in resume but JD needs it
    if len(jd_skills) >= 3 and not has_skills:
        return {
            "score": 15,
            "missing_keywords": jd_skills,
            "rule_violations": [
                "No technical skills present in resume"
            ]
        }

    # 🚨 Clamp high scores
    if score > 85:
        score = 85 - (len(missing) * 1.5)

    # ---------------------------------------------------------
    # FINAL SCORE NORMALIZATION
    # ---------------------------------------------------------
    final_score = int(max(0, min(100, score)))

    return {
        "score": final_score,
        "missing_keywords": list(set(missing)),
        "rule_violations": violations
    }