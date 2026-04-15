"""
backend/services/matcher.py
----------------------------
ATS Scoring Engine — ReZoom AI  v2

Design goal: produce a CONTINUOUS, well-distributed score across the full
0–100 range so that:
  - Irrelevant resumes        →  5 – 25
  - Poor / entry-level match  → 25 – 45
  - Average / partial match   → 45 – 65
  - Good match                → 65 – 80
  - Near-perfect match        → 80 – 95
  - Perfect match             →  95+

Key architectural decisions
---------------------------
1.  LLM extracts JD requirements ONLY (never touches the resume).
2.  Python performs ALL scoring math — no LLM math.
3.  Exact matching PLUS alias/synonym matching to close the "JS ≠ JavaScript"
    gap that caused artificial zero-scores for close resumes.
4.  Proportional penalties replace every hard cap so scores spread naturally.
5.  5-tier experience gradient instead of binary full/cliff.
6.  Resume richness bonus (0–5 pts) differentiates sparse from detailed.
7.  Weighted keyword scoring — the JD's first few terms carry more importance.
"""

from groq import Groq
import os
import json
import re
import math
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SKILL ALIAS MAP
# Key   = canonical form (what the JD might say)
# Value = list of aliases (what the resume might say, or vice-versa)
# Both directions are checked at match time.
# ─────────────────────────────────────────────────────────────────────────────
_ALIASES: dict[str, list[str]] = {
    # Languages
    "javascript":               ["js"],
    "typescript":               ["ts"],
    "python":                   ["py"],
    "c++":                      ["cpp", "c plus plus"],
    "c#":                       ["csharp", "c sharp"],
    ".net":                     ["dotnet", "dot net"],
    "golang":                   ["go"],
    "kotlin":                   ["kt"],
    # Web
    "react":                    ["reactjs", "react.js"],
    "vue":                      ["vuejs", "vue.js"],
    "angular":                  ["angularjs"],
    "node.js":                  ["nodejs", "node"],
    "next.js":                  ["nextjs"],
    "express":                  ["expressjs", "express.js"],
    # Databases
    "postgresql":               ["postgres", "psql"],
    "mongodb":                  ["mongo"],
    "mysql":                    ["my sql"],
    "microsoft sql server":     ["mssql", "sql server"],
    "redis":                    ["redis cache"],
    # Cloud / DevOps
    "amazon web services":      ["aws"],
    "google cloud platform":    ["gcp", "google cloud"],
    "microsoft azure":          ["azure"],
    "kubernetes":               ["k8s"],
    "docker":                   ["dockerfile", "containerization"],
    "ci/cd":                    ["cicd", "continuous integration", "continuous deployment"],
    "github actions":           ["gh actions"],
    # ML / AI
    "machine learning":         ["ml"],
    "deep learning":            ["dl"],
    "natural language processing": ["nlp"],
    "computer vision":          ["cv"],
    "tensorflow":               ["tf"],
    "pytorch":                  ["torch"],
    "large language models":    ["llm", "llms"],
    # Concepts
    "rest apis":                ["rest", "restful", "restful apis", "rest api"],
    "graphql":                  ["graph ql"],
    "microservices":            ["micro services", "micro-services"],
    "object oriented programming": ["oop", "oops"],
    "test driven development":  ["tdd"],
    "agile":                    ["scrum", "kanban"],
    "sql":                      ["structured query language"],
}

# Reverse map: alias → canonical  (built once at import time)
_ALIAS_REVERSE: dict[str, str] = {}
for _canonical, _syns in _ALIASES.items():
    for _syn in _syns:
        _ALIAS_REVERSE[_syn.lower()] = _canonical.lower()


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Safe JSON parse
# ─────────────────────────────────────────────────────────────────────────────
def _safe_parse_resume(resume_data) -> dict:
    if isinstance(resume_data, dict):
        return resume_data
    if isinstance(resume_data, str):
        try:
            parsed = json.loads(resume_data)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Could not parse resume_data string: %s", exc)
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Regex-safe exact token match (handles C++, C#, .NET, etc.)
# ─────────────────────────────────────────────────────────────────────────────
def _exact_match(term: str, text: str) -> bool:
    t = term.strip().lower()
    if not t or not text:
        return False
    escaped = re.escape(t)
    has_special = bool(re.search(r"[^a-z0-9]", t))
    pattern = (
        r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])"
        if has_special
        else r"\b" + escaped + r"\b"
    )
    return bool(re.search(pattern, text))


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Alias-aware match
# Returns (matched: bool, match_type: "exact" | "alias" | "none")
# ─────────────────────────────────────────────────────────────────────────────
def _term_found(term: str, text: str) -> tuple[bool, str]:
    t_lower = term.strip().lower()

    if _exact_match(t_lower, text):
        return True, "exact"

    # Term → known aliases → search in resume
    for alias in _ALIASES.get(t_lower, []):
        if _exact_match(alias, text):
            return True, "alias"

    # Term IS an alias → search for canonical form in resume
    canonical = _ALIAS_REVERSE.get(t_lower)
    if canonical and _exact_match(canonical, text):
        return True, "alias"

    return False, "none"


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: LLM extraction — JD requirements ONLY
# ─────────────────────────────────────────────────────────────────────────────
def _extract_jd_requirements(job_desc: str, client: Groq) -> dict:
    prompt = (
        "You are a strict data-extraction bot. "
        "Read the Job Description below and extract ONLY what is explicitly "
        "stated or strongly implied.\n\n"
        "Return EXACT JSON — no markdown, no explanation, nothing else:\n"
        "{\n"
        '  "jd_req_years": <integer — minimum years of experience, 0 if fresher>,\n'
        '  "jd_keywords": [<up to 10 core domain concepts e.g. "Agile", "Microservices">],\n'
        '  "jd_skills":   [<up to 15 hard tools/languages e.g. "Python", "AWS", "C++">]\n'
        "}\n\n"
        "Rules:\n"
        "  - DO NOT invent skills absent from the JD.\n"
        "  - Use EXACT spelling from the JD (e.g. 'Node.js', not 'NodeJS').\n"
        "  - If no technical skills are mentioned, return empty arrays.\n\n"
        f"Job Description:\n{job_desc}"
    )

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Output pure JSON only. No markdown fences. No preamble.",
            },
            {"role": "user", "content": prompt},
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=512,
    )

    raw = completion.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw).strip()
    parsed = json.loads(raw)

    return {
        "jd_req_years": int(parsed.get("jd_req_years", 0)),
        "jd_keywords":  [str(k).strip() for k in parsed.get("jd_keywords", []) if k],
        "jd_skills":    [str(s).strip() for s in parsed.get("jd_skills",   []) if s],
    }


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: 5-tier experience scoring  (max 20 pts)
# ─────────────────────────────────────────────────────────────────────────────
def _experience_score(estimated: float, required: int) -> tuple[float, str | None]:
    """
    Tier table (% of required years):
      100 %+   → 20 pts   No violation
       75–99 % → 16 pts   Minor note
       50–74 % → 11 pts   Moderate deficit
       25–49 % →  6 pts   Significant deficit
        0–24 % →  2 pts   Severe deficit
    """
    if required <= 0:
        return 20.0, None  # Entry-level / no years stated — full marks

    ratio = estimated / required

    if ratio >= 1.00:
        return 20.0, None
    elif ratio >= 0.75:
        return 16.0, (
            f"EXPERIENCE: JD prefers ~{required} yr(s); "
            f"resume shows ~{estimated:.1f} yr(s) (minor gap)."
        )
    elif ratio >= 0.50:
        return 11.0, (
            f"EXPERIENCE DEFICIT: JD requires ~{required} yr(s); "
            f"resume shows ~{estimated:.1f} yr(s)."
        )
    elif ratio >= 0.25:
        return 6.0, (
            f"EXPERIENCE DEFICIT: JD requires ~{required} yr(s); "
            f"resume shows only ~{estimated:.1f} yr(s) — significant gap."
        )
    else:
        return 2.0, (
            f"SEVERE EXPERIENCE GAP: JD requires ~{required} yr(s); "
            f"resume shows ~{estimated:.1f} yr(s)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Resume richness bonus  (0 – 5 extra points)
# Rewards detailed resumes over sparse ones with the same skill hit-rate.
# ─────────────────────────────────────────────────────────────────────────────
def _richness_bonus(resume: dict) -> float:
    bonus = 0.0

    # Each experience entry with a real description → +0.5 (up to 2 pts)
    for entry in resume.get("experience", [])[:4]:
        if isinstance(entry, dict):
            desc = str(
                entry.get("description", "")
                or entry.get("summary", "")
                or entry.get("highlights", "")
            )
            if len(desc.strip()) > 30:
                bonus += 0.5

    # Skills list depth → up to 2 pts  (0.2 per skill, capped at 2)
    skills = resume.get("tech_skills", [])
    if isinstance(skills, list):
        bonus += min(2.0, len(skills) * 0.2)

    # Professional summary present → +1 pt
    summary = resume.get("summary", "") or resume.get("objective", "")
    if isinstance(summary, str) and len(summary.strip()) > 20:
        bonus += 1.0

    return min(5.0, bonus)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def calculate_match(resume_data, job_desc: str, filename: str) -> dict:
    """
    ATS scoring engine.

    Parameters
    ----------
    resume_data : dict | str   — parsed resume object or its JSON string.
    job_desc    : str          — raw text of the target job description.
    filename    : str          — original filename (logging only, not scored).

    Returns
    -------
    {
        "score":            int   (0–100),
        "missing_keywords": list[str],
        "rule_violations":  list[str],
    }
    """
    resume     = _safe_parse_resume(resume_data)
    score      = 0.0
    violations: list[str] = []
    missing:    list[str] = []

    # ── Guard ─────────────────────────────────────────────────────────────────
    if not job_desc or len(job_desc.strip()) < 10:
        return {
            "score": 5,
            "missing_keywords": [],
            "rule_violations": [
                "FATAL: Job Description is missing or too short. "
                "Cannot perform ATS scan."
            ],
        }

    # =========================================================================
    # BLOCK A — FORMATTING  (15 pts)
    # =========================================================================
    def _non_empty_list(key: str) -> bool:
        val = resume.get(key)
        return isinstance(val, list) and len(val) > 0

    fmt_pts = 15.0
    if not _non_empty_list("education"):
        fmt_pts -= 5.0
        violations.append("FORMATTING: 'education' section is missing or empty.")
    if not _non_empty_list("experience"):
        fmt_pts -= 5.0
        violations.append("FORMATTING: 'work experience' section is missing or empty.")
    if not _non_empty_list("tech_skills"):
        fmt_pts -= 5.0
        violations.append("FORMATTING: 'skills' section is missing or empty.")

    score += max(0.0, fmt_pts)

    # =========================================================================
    # BLOCK B — LLM extracts JD requirements
    # =========================================================================
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "score": 0,
            "missing_keywords": [],
            "rule_violations": ["FATAL: GROQ_API_KEY environment variable not set."],
        }

    client = Groq(api_key=api_key)

    try:
        jd = _extract_jd_requirements(job_desc, client)
    except Exception as exc:
        logger.error("LLM extraction failed for '%s': %s", filename, exc)
        return {
            "score": int(max(0.0, score)),
            "missing_keywords": [],
            "rule_violations": violations + [
                f"ERROR: LLM extraction failed — {exc}. "
                "Keyword/skill scoring skipped."
            ],
        }

    req_years      = jd["jd_req_years"]
    jd_kws         = jd["jd_keywords"]
    jd_skills      = jd["jd_skills"]
    jd_has_content = len(jd_kws) + len(jd_skills) > 0

    # Flatten entire resume dict to one lowercase string for matching
    resume_text_lower = json.dumps(resume, ensure_ascii=False).lower()

    # =========================================================================
    # BLOCK C — KEYWORD MATCHING  (up to 35 pts)
    #
    # Positional weighting: keyword at index i gets weight = 1 + 0.5*e^(-i/3)
    # so the first concept (~1.5x) matters more than the last (~1.0x).
    # Alias matches receive 80% credit instead of 100%.
    # =========================================================================
    matched_kws:    list[str] = []
    unmatched_kws:  list[str] = []
    matched_skills: list[str] = []
    unmatched_skills: list[str] = []
    kw_score    = 0.0
    skill_score = 0.0

    if not jd_has_content:
        violations.append(
            "WARNING: LLM extracted no technical requirements from JD. "
            "Keyword and skill scores set to 0."
        )
    else:
        # ── Keywords ──────────────────────────────────────────────────────────
        if jd_kws:
            w_kws = [1.0 + 0.5 * math.exp(-i / 3) for i in range(len(jd_kws))]
            total_w_kws = sum(w_kws)
            earned_w_kws = 0.0

            for i, kw in enumerate(jd_kws):
                found, mtype = _term_found(kw, resume_text_lower)
                if found:
                    matched_kws.append(kw)
                    earned_w_kws += w_kws[i] * (1.0 if mtype == "exact" else 0.80)
                else:
                    unmatched_kws.append(kw)
                    missing.append(f"Missing Concept: '{kw}'")

            kw_score = (earned_w_kws / total_w_kws) * 35.0

        # ── Skills ────────────────────────────────────────────────────────────
        if jd_skills:
            w_sks = [1.0 + 0.5 * math.exp(-i / 4) for i in range(len(jd_skills))]
            total_w_sks = sum(w_sks)
            earned_w_sks = 0.0

            for i, sk in enumerate(jd_skills):
                found, mtype = _term_found(sk, resume_text_lower)
                if found:
                    matched_skills.append(sk)
                    earned_w_sks += w_sks[i] * (1.0 if mtype == "exact" else 0.80)
                else:
                    unmatched_skills.append(sk)
                    missing.append(f"Missing Tech Skill: '{sk}'")

            skill_score = (earned_w_sks / total_w_sks) * 30.0

        # ── Weight redistribution (if JD only has one dimension) ──────────────
        if not jd_kws and jd_skills:
            # All 65 pts come from skills
            skill_score = (earned_w_sks / total_w_sks) * 65.0
            kw_score    = 0.0
        elif not jd_skills and jd_kws:
            # All 65 pts come from keywords
            kw_score    = (earned_w_kws / total_w_kws) * 65.0
            skill_score = 0.0

        score += kw_score + skill_score

    # =========================================================================
    # BLOCK D — EXPERIENCE  (20 pts, 5-tier gradient)
    # =========================================================================
    experience_list = resume.get("experience", [])
    estimated_years = 0.0

    for entry in experience_list:
        if isinstance(entry, dict):
            title_str = (
                str(entry.get("title",    ""))
                + str(entry.get("role",   ""))
                + str(entry.get("position", ""))
            ).lower()
            if any(w in title_str for w in ("intern", "trainee", "volunteer", "project")):
                estimated_years += 0.5
            else:
                estimated_years += 1.0
        else:
            estimated_years += 0.75

    exp_pts, exp_violation = _experience_score(estimated_years, req_years)
    score += exp_pts
    if exp_violation:
        violations.append(exp_violation)

    # =========================================================================
    # BLOCK E — RESUME RICHNESS BONUS  (0 – 5 pts)
    # =========================================================================
    richness = _richness_bonus(resume)
    score += richness

    # =========================================================================
    # BLOCK F — PROPORTIONAL FAILSAFES
    # No more hard cliffs. Every penalty scales continuously.
    # =========================================================================
    raw_score = score  # stay as float until the very end

    total_req     = len(jd_kws) + len(jd_skills)
    total_matched = len(matched_kws) + len(matched_skills)

    # ── Failsafe 1: Relevance multiplier  ────────────────────────────────────
    # Replaces the old hard "nuke to 15" cap.
    # A resume with 0/N matches is multiplied down to near-zero.
    # A resume with 1/N matches gets partial credit.
    if total_req >= 3:
        relevance_ratio = total_matched / total_req
        if relevance_ratio == 0.0:
            # Hard zero matches → keep only formatting + tiny signal (max ~18)
            raw_score = min(raw_score, 5.0 + (fmt_pts / 15.0) * 13.0)
            violations.append(
                "FATAL: Resume matches zero technical requirements. "
                "This resume appears completely irrelevant to the role."
            )
        elif relevance_ratio < 0.20:
            # Very few matches → drag score down proportionally
            # multiplier ranges 0.40 – 0.65 as relevance_ratio goes 0 → 0.20
            multiplier = 0.40 + (relevance_ratio / 0.20) * 0.25
            raw_score  = raw_score * multiplier
            violations.append(
                f"RELEVANCE WARNING: Only {total_matched}/{total_req} "
                "technical requirements matched — score suppressed."
            )

    # ── Failsafe 2: Proportional missing-skills penalty  ─────────────────────
    # Old: flat -20 when missing >= 4.
    # New: penalty = (missing_ratio) * 18, applied only when score > 55.
    total_missing_count = len(unmatched_kws) + len(unmatched_skills)
    if total_req > 0 and total_missing_count > 0:
        missing_ratio      = total_missing_count / total_req
        proportional_deduction = missing_ratio * 18.0
        if raw_score > 55:
            raw_score -= proportional_deduction

    # ── Failsafe 3: Soft ceiling for high scores  ─────────────────────────────
    # > 85 requires both a high match rate AND adequate experience.
    high_match  = total_req > 0 and (total_matched / total_req) >= 0.85
    enough_exp  = (req_years <= 0) or (estimated_years >= req_years * 0.9)

    if raw_score > 85:
        if not high_match and not enough_exp:
            raw_score = 72 + (raw_score - 85) * 0.3   # compress → 72–76 band
        elif not high_match or not enough_exp:
            raw_score = 80 + (raw_score - 85) * 0.4   # compress → 80–82 band

    # ── Failsafe 4: Perfect score guard  ─────────────────────────────────────
    if raw_score >= 100 and (len(missing) > 0 or exp_violation):
        raw_score = 95.0

    # ── Final clamp ───────────────────────────────────────────────────────────
    final_score = max(0, min(100, int(round(raw_score))))

    logger.info(
        "[ATS] file='%s' final=%d  raw=%.1f  kw=%d/%d  sk=%d/%d  "
        "exp=%.1f/%d  richness=%.1f  missing=%d  violations=%d",
        filename, final_score, score,
        len(matched_kws), len(jd_kws),
        len(matched_skills), len(jd_skills),
        estimated_years, req_years,
        richness, len(missing), len(violations),
    )

    return {
        "score":            final_score,
        "missing_keywords": missing,
        "rule_violations":  violations,
    }