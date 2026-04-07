def get_suggestions(resume, job):
    # fallback if no API
    return {
        "suggestions": [
            "Add more job-relevant keywords",
            "Highlight UI/UX projects more clearly",
            "Reduce unrelated skills",
            "Use action verbs (Designed, Built, Improved)"
        ]
    }