import os
import subprocess
import uuid

def generate_latex(data):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_name = data.get("template", "base")
    template_file = f"{template_name}.tex"
    template_path = os.path.join(base_dir, "templates", template_file)
    
    if not os.path.exists(template_path):
        template_path = os.path.join(base_dir, "templates", "base.tex")

    output_dir = os.path.join(base_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    unique_id = str(uuid.uuid4())[:8]
    tex_filename = os.path.join(output_dir, f"resume_{unique_id}.tex")
    pdf_filename = f"resume_{unique_id}.pdf"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            tex_content = file.read()
            
        tex_content = tex_content.replace("<<NAME>>", escape_latex(data.get("name", "Applicant")))
        tex_content = tex_content.replace("<<EMAIL>>", escape_latex(data.get("email", "email@example.com")))
        tex_content = tex_content.replace("<<EDUCATION>>", escape_latex(data.get("education", "")))
        
        skills = data.get("skills", "").split(",")
        skills_latex = "\\begin{itemize}\n"
        for skill in skills:
            if skill.strip():
                skills_latex += f"    \\item {escape_latex(skill.strip())}\n"
        skills_latex += "\\end{itemize}"
        
        tex_content = tex_content.replace("<<SKILLS>>", skills_latex)
        tex_content = tex_content.replace("<<EXPERIENCE>>", escape_latex(data.get("experience", "")))
        
        with open(tex_filename, 'w', encoding='utf-8') as file:
            file.write(tex_content)
            
        process = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", f"-output-directory={output_dir}", tex_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            raise RuntimeError("LaTeX compilation failed. Ensure pdflatex is configured properly.")
            
        return f"/outputs/{pdf_filename}"
        
    except FileNotFoundError:
        raise FileNotFoundError("pdflatex executable not found. A TeX distribution is required in the system PATH.")
    except Exception as e:
        raise Exception(f"Document generation exception: {str(e)}")

def escape_latex(text):
    chars = {'&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}'}
    for k, v in chars.items(): text = text.replace(k, v)
    return text