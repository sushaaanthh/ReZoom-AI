import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# Absolute pathing to guarantee the Landing Page loads
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

from services.parser import extract_and_structure
from services.optimizer import optimize_resume_content
from services.matcher import calculate_match
from services.latex import generate_latex

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/parse', methods=['POST'])
def parse_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        parsed_data = extract_and_structure(request.files['file'])
        return jsonify({"data": parsed_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/optimize', methods=['POST'])
def optimize_route():
    data = request.json
    try:
         optimized_data = optimize_resume_content(data['parsed_resume'], data['job_description'])
         return jsonify({"data": optimized_data})
    except Exception as e:
         return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_route():
    data = request.json
    try:
        match_results = calculate_match(data['resume_data'], data['job_description'], data['filename'])
        return jsonify(match_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_route():
    data = request.json
    try:
        pdf_file_path = generate_latex(data)
        return send_file(pdf_file_path, as_attachment=True, download_name='ReZoom_Resume.pdf', mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)