from groq import Groq
import os
import json

def _analyze_jd(client: Groq, job_desc: str) -> dict:
    """
    Phase 1 — Agentic JD Analysis.
    Extracts ranked requirements from the Job Description BEFORE any resume
    content is touched. This grounding step prevents hallucination and gives
    the optimizer concrete, ranked targets to align against.
    """
    prompt = f"""
    You are a Job Description analyst. Deeply analyze the following Job Description
    and extract structured, ranked requirements.

    INSTRUCTIONS:
    - Rank ALL technical skills/tools by how explicitly and frequently they are 
      mentioned (rank 1 = most critical).
    - Identify the 3 most important "impact themes" (e.g., "scalability", 
      "cross-functional collaboration", "cost reduction") the employer cares about.
    - Extract exact action verbs used in the JD (e.g., "architected", "led", "deployed").
    - Identify the seniority signal: junior / mid / senior / lead.

    OUTPUT ONLY this JSON:
    {{
        "ranked_skills": [
            {{"rank": 1, "skill": "Python", "context": "why it matters from JD"}},
            {{"rank": 2, "skill": "Docker", "context": "why it matters from JD"}}
        ],
        "impact_themes": ["theme1", "theme2", "theme3"],
        "preferred_verbs": ["verb1", "verb2", "verb3"],
        "seniority": "mid",
        "role_core": "One sentence: what this role fundamentally does"
    }}

    JOB DESCRIPTION:
    {job_desc}
    """
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise JD analyst. Output ONLY valid JSON. "
                    "No markdown, no explanation, no preamble."
                )
            },
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        temperature=0.1,  # Near-deterministic for analysis
    )
    return json.loads(completion.choices[0].message.content.strip())


def _build_optimizer_prompt(parsed_data: dict, job_desc: str, jd_analysis: dict) -> str:
    """
    Constructs a grounded, multi-constraint optimizer prompt using the
    Phase 1 JD analysis as an explicit reference anchor.
    """
    ranked_skills_str = "\n".join(
        f"  Rank {s['rank']}: {s['skill']} — {s['context']}"
        for s in jd_analysis.get("ranked_skills", [])
    )
    impact_themes_str = ", ".join(jd_analysis.get("impact_themes", []))
    preferred_verbs_str = ", ".join(jd_analysis.get("preferred_verbs", []))
    role_core = jd_analysis.get("role_core", "")
    seniority = jd_analysis.get("seniority", "mid")

    return f"""
You are a senior Resume Strategist. Your ONLY job is to restructure and rephrase
the provided resume data to maximally align with the target role. You are NOT a
content generator — you are a content RERANKER and REPHRASER.

═══════════════════════════════════════════
GROUNDING CONTEXT (from JD Analysis — treat as ground truth)
═══════════════════════════════════════════
Role Core:        {role_core}
Seniority Signal: {seniority}
Impact Themes:    {impact_themes_str}
Preferred Verbs:  {preferred_verbs_str}

Ranked Technical Requirements (use this order to sort tech_skills):
{ranked_skills_str}

═══════════════════════════════════════════
RESTRUCTURING RULES — FOLLOW EXACTLY
═══════════════════════════════════════════

RULE 1 — TECH SKILLS REORDERING (most important rule):
  - Sort the `tech_skills` ARRAY so that the category containing the highest-ranked
    skills (from the ranked list above) appears FIRST.
  - Within each category's `skills` string, list higher-ranked skills before lower-ranked ones.
  - Categories with zero overlap with ranked skills go LAST.

RULE 2 — EXPERIENCE BULLET REWRITING:
  - Rewrite each description to echo the EXACT impact themes: {impact_themes_str}
  - Start bullets with verbs from this list where truthful: {preferred_verbs_str}
  - Map quantifiable results to themes (e.g., if "scalability" is a theme and the
    candidate improved performance, emphasize that angle).
  - Keep seniority language consistent with: {seniority}

RULE 3 — ZERO HALLUCINATION GUARDRAILS:
  - You MAY reorder, rephrase, and reframe — you may NOT invent.
  - If a skill is not in the original data, do NOT add it.
  - If a job role is not in the original experience, do NOT create one.
  - If you cannot find a truthful way to map an experience to the JD, leave it
    rephrased generically — do NOT fabricate metrics or technologies.
  - Treat the original data as a HARD CONTRACT. Every output item must trace
    back to an input item.

RULE 4 — JSON SCHEMA INTEGRITY:
  - Output MUST match this schema exactly. No extra keys. No missing keys.
  - `experience[].description` must be a single string of newline-separated bullets
    starting with "• ".
  - `tech_skills[].skills` must be a comma-separated string (not an array).
  - `soft_skills` must be an array of strings.

═══════════════════════════════════════════
OUTPUT JSON SCHEMA (do not deviate):
═══════════════════════════════════════════
{{
    "experience": [
        {{
            "company": "Exact company & role from input — DO NOT CHANGE",
            "start": "Exact date from input",
            "end": "Exact date from input",
            "description": "• Rewritten bullet 1\\n• Rewritten bullet 2\\n• Rewritten bullet 3"
        }}
    ],
    "tech_skills": [
        {{
            "type": "Category Name from input — DO NOT RENAME",
            "skills": "Skill1, Skill2, Skill3 (reordered by JD relevance)"
        }}
    ],
    "soft_skills": ["Skill 1", "Skill 2"]
}}

═══════════════════════════════════════════
RESUME DATA TO PROCESS (this is your ONLY source of truth):
═══════════════════════════════════════════
Target Job Description:
{job_desc}

Original Experience:
{json.dumps(parsed_data.get('experience', []), indent=2)}

Original Tech Skills:
{json.dumps(parsed_data.get('tech_skills', []), indent=2)}

Original Soft Skills:
{json.dumps(parsed_data.get('soft_skills', []), indent=2)}
"""


def _validate_output_schema(optimized: dict, original: dict) -> dict:
    """
    Post-processing guard: ensures the LLM didn't drop fields, add phantom
    entries, or corrupt the schema. Falls back gracefully per field.
    """
    original_companies = {
        e.get("company", "").lower()
        for e in original.get("experience", [])
    }
    original_categories = {
        s.get("type", "").lower()
        for s in original.get("tech_skills", [])
    }

    # Purge any experience entries the LLM hallucinated
    validated_experience = [
        entry for entry in optimized.get("experience", [])
        if entry.get("company", "").lower() in original_companies
    ]

    # Purge any skill categories the LLM hallucinated
    validated_tech_skills = [
        cat for cat in optimized.get("tech_skills", [])
        if cat.get("type", "").lower() in original_categories
    ]

    # Fall back to original if the LLM dropped entries entirely
    if not validated_experience:
        validated_experience = original.get("experience", [])

    if not validated_tech_skills:
        validated_tech_skills = original.get("tech_skills", [])

    return {
        "experience": validated_experience,
        "tech_skills": validated_tech_skills,
        "soft_skills": optimized.get("soft_skills") or original.get("soft_skills", []),
    }


def optimize_resume_content(parsed_data: dict, job_desc: str) -> dict:
    """
    Agentic two-phase resume optimizer.

    Phase 1 — JD Analysis:
        Extracts ranked skills, impact themes, and preferred verbs from the
        Job Description. This grounding step gives the optimizer concrete,
        ranked targets instead of letting it infer vaguely from raw text.

    Phase 2 — Grounded Optimization:
        Uses the Phase 1 analysis as an explicit reference anchor to reorder
        tech_skills by relevance rank and rewrite experience bullets to echo
        the JD's specific language and themes.

    Post-processing:
        Schema validation strips any hallucinated entries before returning.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is missing from environment variables.")

    client = Groq(api_key=api_key)

    # ── Phase 1: Analyze the JD into ranked, structured requirements ──────────
    try:
        jd_analysis = _analyze_jd(client, job_desc)
    except Exception as e:
        raise RuntimeError(f"Phase 1 (JD Analysis) failed: {str(e)}")

    # ── Phase 2: Optimize resume against the grounded JD analysis ────────────
    optimizer_prompt = _build_optimizer_prompt(parsed_data, job_desc, jd_analysis)

    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a resume restructuring engine. "
                        "Output ONLY a valid JSON object. "
                        "No markdown fences. No commentary. No extra keys."
                    ),
                },
                {"role": "user", "content": optimizer_prompt},
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.15,
        )

        raw_content = completion.choices[0].message.content.strip()

        # Safety strip for any stray markdown fences
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0]

        optimized_data = json.loads(raw_content.strip())

    except Exception as e:
        raise RuntimeError(f"Phase 2 (Optimization) failed: {str(e)}")

    # ── Post-processing: Validate schema, strip hallucinations ───────────────
    return _validate_output_schema(optimized_data, parsed_data)