import os
import subprocess
import uuid

def generate_latex(data):
    """
    Fills a LaTeX template with dynamic data and compiles it to a PDF.
    """
    # Define directory paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, "templates", "base.tex")
    output_dir = os.path.join(base_dir, "outputs")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filenames to prevent overwriting
    unique_id = str(uuid.uuid4())[:8]
    tex_filename = os.path.join(output_dir, f"resume_{unique_id}.tex")
    pdf_filename = f"resume_{unique_id}.pdf"
    
    try:
        # 1. Read the base template
        with open(template_path, 'r', encoding='utf-8') as file:
            tex_content = file.read()
            
        # 2. Replace placeholders with actual data
        tex_content = tex_content.replace("<<NAME>>", escape_latex(data.get("name", "Your Name")))
        tex_content = tex_content.replace("<<EMAIL>>", escape_latex(data.get("email", "email@example.com")))
        tex_content = tex_content.replace("<<PHONE>>", escape_latex(data.get("phone", "")))
        
        # Format skills as a LaTeX itemized list
        skills = data.get("skills", "").split(",")
        skills_latex = "\\begin{itemize}\n"
        for skill in skills:
            if skill.strip():
                skills_latex += f"    \\item {escape_latex(skill.strip())}\n"
        skills_latex += "\\end{itemize}"
        
        tex_content = tex_content.replace("<<SKILLS>>", skills_latex)
        tex_content = tex_content.replace("<<EXPERIENCE>>", escape_latex(data.get("experience", "")))
        
        # 3. Write the filled template to a new .tex file
        with open(tex_filename, 'w', encoding='utf-8') as file:
            file.write(tex_content)
            
        # 4. Compile the .tex file to PDF
        # We run it twice to ensure formatting and references resolve correctly
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={output_dir}", tex_filename],
                stdout=subprocess.DEVNULL, # Suppress terminal output for clean logs
                stderr=subprocess.DEVNULL,
                check=True
            )
            
        # Optional: Clean up auxiliary files (.aux, .log)
        clean_up_aux_files(output_dir, unique_id)
            
        return f"/outputs/{pdf_filename}"
        
    except FileNotFoundError:
        print("CRITICAL ERROR: 'pdflatex' command not found. Ensure TeX Live/MiKTeX is installed and in your PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"LaTeX Compilation Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in LaTeX generation: {e}")
        return None

def escape_latex(text):
    """
    Escapes special LaTeX characters to prevent compilation errors.
    """
    chars = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', 
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'
    }
    # Escape backslash first to avoid double escaping
    text = text.replace('\\', chars['\\'])
    for k, v in chars.items():
        if k != '\\':
            text = text.replace(k, v)
    return text

def clean_up_aux_files(directory, file_id):
    """Removes messy .log and .aux files generated during LaTeX compilation."""
    for ext in ['.log', '.aux']:
        file_path = os.path.join(directory, f"resume_{file_id}{ext}")
        if os.path.exists(file_path):
            os.remove(file_path)