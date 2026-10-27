"""
AI Code Review System - Flask Web Application & REST API
CEP Project AD3 - AI Code Review System
"""

import sys
import os
from flask import Flask, render_template, request, jsonify

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import AICodeReviewer

app = Flask(__name__)
reviewer = AICodeReviewer(max_func_lines=25, max_complexity=10, max_nesting=3)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/review", methods=["POST"])
def api_review():
    """REST API endpoint for reviewing Python code (consumed by UI, CLI, or VS Code extension)."""
    data = request.get_json(force=True, silent=True) or {}
    source_code = data.get("code", "")
    filename = data.get("filename", "<editor>")

    if not source_code.strip():
        return jsonify({"error": "No code provided"}), 400

    report = reviewer.review_code(source_code, filename=filename)
    return jsonify(report.to_dict())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 AI Code Review System Web App running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
