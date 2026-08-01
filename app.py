import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
PROVIDER_URL = os.environ.get("PROVIDER_URL", "https://httpbin.org/post")


def build_payload(body: dict) -> dict:
    return {"to": body.get("to"), "text": body.get("text", "")[:280]}


@app.post("/notify")
def notify():
    key = os.environ.get("PROVIDER_API_KEY")
    if not key:
        return jsonify({"error": "PROVIDER_API_KEY not configured"}), 500
    r = requests.post(PROVIDER_URL, json=build_payload(request.get_json(force=True)),
                      headers={"Authorization": f"Bearer {key}"}, timeout=10)
    return jsonify({"status": r.status_code})
