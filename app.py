
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")


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

    if len(message) > 20000:
        return jsonify({"error": "Message is too long, Sir."}), 413

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        app.logger.error("OPENROUTER_API_KEY is not configured.")
        return jsonify({"error": "AI service is not configured."}), 500

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are JARVIS, a helpful AI assistant. "
                    "Address the user respectfully as Sir. "
                    "Reply in the language the user uses. "
                    "Be clear, accurate, and helpful."
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
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=90
        )

        if response.status_code != 200:
            app.logger.error(
                "OpenRouter returned HTTP %s: %s",
                response.status_code,
                response.text[:500]
            )
            return jsonify({
                "error": "AI request failed. Please try again later."
            }), 502

        result = response.json()
        choices = result.get("choices") or []
        if not choices:
            return jsonify({"error": "AI returned no answer."}), 502

        reply = (choices[0].get("message") or {}).get("content", "")

        if isinstance(reply, list):
            reply = " ".join(
                part.get("text", "")
                for part in reply
                if isinstance(part, dict)
            )

        if not isinstance(reply, str) or not reply.strip():
            return jsonify({"error": "AI returned an empty response."}), 502

        return jsonify({"reply": reply.strip()})

    except requests.Timeout:
        app.logger.warning("OpenRouter request timed out.")
        return jsonify({"error": "AI took too long to respond. Please try again."}), 504

    except requests.RequestException:
        app.logger.exception("OpenRouter connection failed.")
        return jsonify({
            "error": "Could not connect to the AI service. Please try again."
        }), 502

    except (ValueError, KeyError, TypeError):
        app.logger.exception("Invalid OpenRouter response.")
        return jsonify({"error": "Invalid response from AI service."}), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
