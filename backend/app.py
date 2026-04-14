import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from services.parser import extract_and_structure
from services.matcher import calculate_match
from services.latex import generate_latex
from services.optimizer import optimize_resume_content

load_dotenv()

frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=frontend_folder, static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return jsonify({"error": "File not found"}), 404

@app.route('/parse', methods=['POST'])
def parse_resume():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        structured_data = extract_and_structure(file)
        return jsonify({"data": structured_data, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/optimize', methods=['POST'])
def optimize_job():
    try:
        data = request.json
        parsed_resume = data.get('parsed_resume')
        job_desc = data.get('job_description')
        
        optimized_data = optimize_resume_content(parsed_resume, job_desc)
        return jsonify({"data": optimized_data, "status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/match', methods=['POST'])
def match_job():
    try:
        data = request.json
        resume_text = data.get('resume', '')
        job_desc = data.get('job_description', '')
        
        match_results = calculate_match(resume_text, job_desc)
        return jsonify(match_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        pdf_path = generate_latex(data) 
        return jsonify({"message": "PDF generated successfully", "download_url": pdf_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/outputs/<filename>')
def serve_pdf(filename):
    outputs_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    return send_from_directory(outputs_dir, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)