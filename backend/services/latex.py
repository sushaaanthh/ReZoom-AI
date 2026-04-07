import os

def generate_pdf(data):
    with open("templates/base.tex", "r") as f:
        template = f.read()

    tex = template.replace("NAME_PLACEHOLDER", data.get("name", "Your Name"))
    tex = tex.replace("SKILLS_PLACEHOLDER", ", ".join(data.get("skills", [])))
    tex = tex.replace("EXPERIENCE_PLACEHOLDER", data.get("experience", ""))
    tex = tex.replace("EDUCATION_PLACEHOLDER", data.get("education", ""))

    os.makedirs("outputs", exist_ok=True)

    tex_path = "outputs/resume.tex"

    with open(tex_path, "w") as f:
        f.write(tex)

    os.system(f"pdflatex -output-directory=outputs {tex_path}")

    return "outputs/resume.pdf"