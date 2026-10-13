
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "JARVIS Cloud",
        "status": "online"
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ready"})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Please enter a message, Sir."
        }), 400

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({
            "error": "Gemini API key is not configured."
        }), 500

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-2.5-flash:generateContent"
    )

    payload = {
        "system_instruction": {
            "parts": [{
                "text": (
                    "You are JARVIS, a helpful AI assistant. "
                    "Address the user respectfully as Sir. "
                    "Reply in the language the user uses."
                )
            }]
        },
        "contents": [{
            "parts": [{"text": message}]
        }]
    }

    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=60
        )

        result = response.json()

        if response.status_code != 200:
            app.logger.error(
                "Gemini API error: %s", response.status_code
            )
            return jsonify({
                "error": "Gemini AI request failed. Please check the API setup."
            }), 502

        reply = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not reply:
            return jsonify({
                "error": "Gemini returned an empty response."
            }), 502

        return jsonify({"reply": reply})

    except requests.RequestException:
        app.logger.exception("Gemini connection failed")
        return jsonify({
            "error": "Could not connect to Gemini AI. Please try again."
        }), 502

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
