
import os
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
SYSTEM_PROMPT = (
    "You are JARVIS, a helpful AI assistant. "
    "Address the user respectfully as Sir. "
    "Reply in the language the user uses. "
    "Be clear, accurate, and helpful."
)


def call_ai(messages):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        app.logger.error("OPENROUTER_API_KEY is not configured.")
        return None, ({"error": "AI service is not configured."}, 500)

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Title": "JARVIS Cloud"
            },
            json={"model": MODEL, "messages": messages},
            timeout=90
        )

        if response.status_code != 200:
            app.logger.error(
                "OpenRouter HTTP %s: %s",
                response.status_code, response.text[:500]
            )
            return None, (
                {"error": "AI request failed. Check model support and try again."},
                502
            )

        result = response.json()
        choices = result.get("choices") or []
        if not choices:
            return None, ({"error": "AI returned no answer."}, 502)

        reply = (choices[0].get("message") or {}).get("content", "")
        if isinstance(reply, list):
            reply = " ".join(
                part.get("text", "")
                for part in reply if isinstance(part, dict)
            )

        if not isinstance(reply, str) or not reply.strip():
            return None, ({"error": "AI returned an empty response."}, 502)

        return reply.strip(), None

    except requests.Timeout:
        return None, (
            {"error": "AI took too long to respond. Please try again."}, 504
        )
    except requests.RequestException:
        app.logger.exception("OpenRouter connection failed.")
        return None, ({"error": "Could not connect to AI service."}, 502)
    except (ValueError, KeyError, TypeError):
        app.logger.exception("Invalid OpenRouter response.")
        return None, ({"error": "Invalid response from AI service."}, 502)


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Image is too large. Please use an image under 8 MB."}), 413


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

    reply, error = call_ai([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ])
    if error:
        return jsonify(error[0]), error[1]
    return jsonify({"reply": reply})


@app.route("/ask-image", methods=["POST"])
def ask_image():
    if "image" not in request.files:
        return jsonify({"error": "Please select an image first, Sir."}), 400

    image = request.files["image"]
    question = request.form.get(
        "message", "Describe this image clearly."
    ).strip()

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if image.mimetype not in allowed_types:
        return jsonify({
            "error": "Please choose a JPG, PNG, or WEBP image."
        }), 415

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"error": "The selected image is empty."}), 400

    if len(image_bytes) > 7 * 1024 * 1024:
        return jsonify({"error": "Please use an image under 7 MB."}), 413

    encoded = base64.b64encode(image_bytes).decode("ascii")
    mime_type = image.mimetype
    image_url = f"data:{mime_type};base64,{encoded}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question or "Describe this image."},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }
    ]

    reply, error = call_ai(messages)
    if error:
        return jsonify(error[0]), error[1]
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
