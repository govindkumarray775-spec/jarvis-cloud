
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"name": "JARVIS Cloud", "status": "online"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ready"})

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Please enter a message, Sir."}), 400

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "OpenRouter API key is not configured."}), 500

    url = "https://openrouter.ai/api/v1/chat/completions"

    payload = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are JARVIS, a helpful AI assistant. "
                    "Address the user respectfully as Sir. "
                    "Reply in the language the user uses."
                )
            },
            {"role": "user", "content": message}
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "JARVIS Cloud"
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=90
        )

        if response.status_code != 200:
            app.logger.error(
                "OpenRouter error %s: %s",
                response.status_code,
                response.text[:1000]
            )
            return jsonify({
                "error": "OpenRouter request failed. Check Render logs."
            }), 502

        result = response.json()
        reply = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if isinstance(reply, list):
            reply = " ".join(
                part.get("text", "")
                for part in reply
                if isinstance(part, dict)
            )

        if not reply:
            return jsonify({"error": "AI returned an empty response."}), 502

        return jsonify({"reply": reply})

    except requests.RequestException:
        app.logger.exception("OpenRouter connection failed")
        return jsonify({
            "error": "Could not connect to OpenRouter. Please try again."
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
