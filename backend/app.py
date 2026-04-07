from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from services.parser import extract_text
from services.matcher import calculate_match
from services.latex import generate_latex
import os

app = Flask(__name__)
CORS(app) # Allow frontend to communicate with backend

@app.route('/parse', methods=['POST'])
def parse_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    text = extract_text(file)
    return jsonify({"extracted_text": text, "status": "success"})

@app.route('/match', methods=['POST'])
def match_job():
    data = request.json
    resume_text = data.get('resume', '')
    job_desc = data.get('job_description', '')
    
    match_results = calculate_match(resume_text, job_desc)
    return jsonify(match_results)

@app.route('/generate', methods=['POST'])
def generate_pdf():
    data = request.json
    # In a real app, this compiles base.tex via pdflatex
    pdf_path = generate_latex(data) 
    return jsonify({"message": "PDF generated successfully", "download_url": "/downloads/resume.pdf"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)