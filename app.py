from flask import Flask, request, jsonify, render_template
from google import genai
import time
from google.genai import errors
import os

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Set it before running app.py."
    )

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are CYD AI, a friendly personal assistant on an ESP32 touchscreen.
Give accurate, helpful answers using simple English.
Keep responses short because the screen is small.
"""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if len(message) > 2000:
        return jsonify({"error": "Message is too long"}), 400

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"{SYSTEM_PROMPT}\n\nUser: {message}"
            )

            return jsonify({
                "reply": response.text or "No response received."
            })

        except errors.APIError as e:
            if e.code == 503 and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue

            app.logger.exception("Gemini API request failed")
            return jsonify({
                "error": f"Gemini is temporarily unavailable (HTTP {e.code}). Please try again."
            }), 502

        except Exception:
            app.logger.exception("Unexpected Gemini error")
            return jsonify({
                "error": "An unexpected error occurred. Check the Flask terminal."
            }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)