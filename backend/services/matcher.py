def match_resume(resume, job):
    resume_words = set(resume.lower().split())
    job_words = set(job.lower().split())

    matched = resume_words & job_words
    missing = job_words - resume_words

    score = int((len(matched) / (len(job_words) + 1)) * 100)

    return {
        "score": score,
        "matched": list(matched)[:20],
        "missing": list(missing)[:20]
    }


def prioritize_sections(sections, job):
    job_words = set(job.lower().split())

    scored_sections = []

    for section in sections:
        words = set(section["content"].lower().split())
        relevance = len(words & job_words)

        scored_sections.append({
            "title": section["title"],
            "content": section["content"],
            "score": relevance
        })

    sorted_sections = sorted(scored_sections, key=lambda x: x["score"], reverse=True)

    return sorted_sections