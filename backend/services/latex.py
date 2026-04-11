import os
import subprocess
import uuid

def generate_latex(data):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # 1. Determine which template to use based on frontend input
    template_name = data.get("template", "base")
    template_file = f"{template_name}.tex"
    template_path = os.path.join(base_dir, "templates", template_file)
    
    # Fallback if template doesn't exist
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
            
        # Data Injection
        tex_content = tex_content.replace("<<NAME>>", escape_latex(data.get("name", "Your Name")))
        tex_content = tex_content.replace("<<EMAIL>>", escape_latex(data.get("email", "email@example.com")))
        
        # Handle Education
        edu_text = escape_latex(data.get("education", ""))
        tex_content = tex_content.replace("<<EDUCATION>>", edu_text)
        
        # Handle Skills list
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
            
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={output_dir}", tex_filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            
        return f"/outputs/{pdf_filename}"
        
    except Exception as e:
        print(f"Error in LaTeX generation: {e}")
        return None

def escape_latex(text):
    chars = {'&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}'}
    for k, v in chars.items(): text = text.replace(k, v)
    return text