from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import errors
import os
import time

app = Flask(__name__)

GEMINI_API_KEY = "AIzaSyA9lKEaTathIhT178O2fygvCXixJcGNb7o"

api_key = os.environ.get(GEMINI_API_KEY)

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

    if not isinstance(message, str):
        return jsonify({"error": "Message must be text."}), 400

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    if len(message) > 2000:
        return jsonify({"error": "Message is too long."}), 400

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "max_output_tokens": 250,
                },
                contents=message,
            )

            return jsonify({
                "reply": response.text or "No response received."
            })

        except errors.APIError as e:
            app.logger.error(
                "Gemini API error: code=%s, message=%s",
                e.code,
                str(e),
            )

            if e.code == 503 and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue

            return jsonify({
                "error": f"Gemini request failed (HTTP {e.code}). Check the Flask terminal."
            }), 502

        except Exception:
            app.logger.exception("Unexpected Gemini error")
            return jsonify({
                "error": "An unexpected error occurred. Check the Flask terminal."
            }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)
