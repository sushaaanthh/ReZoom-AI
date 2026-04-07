from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from services.parser import parse_resume
from services.matcher import match_resume, prioritize_sections
from services.latex import generate_pdf
from services.ai_suggestions import get_suggestions

app = Flask(__name__)
CORS(app)

@app.route("/parse", methods=["POST"])
def parse():
    file = request.files.get("file")

    if not file:
        return {"error": "No file uploaded"}, 400

    data = parse_resume(file)
    return jsonify(data)

@app.route("/match", methods=["POST"])
def match():
    data = request.json

    result = match_resume(data["resume"], data["job"])
    return jsonify(result)

@app.route("/prioritize", methods=["POST"])
def prioritize():
    data = request.json

    result = prioritize_sections(data["sections"], data["job"])
    return jsonify(result)

@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.json

    suggestions = get_suggestions(data["resume"], data["job"])
    return jsonify(suggestions)

@app.route("/generate", methods=["POST"])
def generate():
    pdf = generate_pdf(request.json)
    return send_file(pdf, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)