import os
import subprocess
from jinja2 import Environment, FileSystemLoader

def escape_latex(text):
    if not isinstance(text, str): return text
    chars = { '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\^{}', '\\': r'\textbackslash{}'}
    for k, v in chars.items(): text = text.replace(k, v)
    return text

def clean_data(data):
    if isinstance(data, dict): return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list): return [clean_data(v) for v in data]
    return escape_latex(data)

def generate_latex(data):
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), '..', 'templates')), block_start_string=r'\BLOCK{', block_end_string='}', variable_start_string=r'\VAR{', variable_end_string='}')
    template_name = data.get('template', 'classic') + '.tex'
    template = env.get_template(template_name)
    
    safe_data = clean_data(data)
    rendered_tex = template.render(**safe_data)
    
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    tex_path = os.path.join(output_dir, 'resume.tex')
    pdf_path = os.path.join(output_dir, 'resume.pdf')
    
    # Delete old PDF to ensure we don't serve a stale one
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(rendered_tex)
        
    # RUN COMPILER: We removed check=True so Python doesn't panic over minor LaTeX warnings!
    process = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'resume.tex'], cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Check if the PDF actually exists, regardless of what LaTeX complained about
    if not os.path.exists(pdf_path):
        error_msg = process.stdout.decode('utf-8', errors='ignore')
        raise RuntimeError(f"LaTeX failed to generate PDF completely. Log: {error_msg[-500:]}")
        
    return pdf_path