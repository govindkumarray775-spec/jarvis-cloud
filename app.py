
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
        return jsonify({"error": "Please enter a message, Sir."}), 400

    # Temporary response to test the cloud connection
    reply = (
        "Yes Sir, I received your message: "
        + message
        + ". Cloud connection is working, but AI is not connected yet."
    )

    return jsonify({"reply": reply})

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
