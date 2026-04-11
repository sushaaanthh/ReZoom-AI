from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from services.parser import extract_text
from services.matcher import calculate_match
from services.latex import generate_latex
import os

app = Flask(__name__)
CORS(app)

@app.route('/parse', methods=['POST'])
def parse_resume():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files['file']
        text = extract_text(file)
        return jsonify({"extracted_text": text, "status": "success"})
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
    return send_from_directory(outputs_dir, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)