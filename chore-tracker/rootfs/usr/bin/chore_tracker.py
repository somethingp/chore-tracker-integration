#!/usr/bin/env python3
"""
Chore Tracker — Home Assistant Add-on API
Stores state in /data/chores.json (persisted by HA across restarts).
"""

import json
import os
import time
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

DATA_FILE = Path("/data/chores.json")
PORT = 8787

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Default chores written on first boot ─────────────────────────────────────
DEFAULT_STATE = {
    "chores": [
        {"id": 1, "name": "Vacuum living room",  "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
        {"id": 2, "name": "Take out trash",       "freqDays": 3,  "lastDone": None, "lastBy": None, "history": []},
        {"id": 3, "name": "Clean kitchen",        "freqDays": 2,  "lastDone": None, "lastBy": None, "history": []},
        {"id": 4, "name": "Wipe bathroom",        "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
        {"id": 5, "name": "Mop floors",           "freqDays": 14, "lastDone": None, "lastBy": None, "history": []},
        {"id": 6, "name": "Change bed sheets",    "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
    ],
    "nextId": 7,
}

# ── Persistence helpers ───────────────────────────────────────────────────────

def load_state() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_STATE))  # deep copy


def save_state(state: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, indent=2))


def find_chore(state: dict, chore_id: int):
    return next((c for c in state["chores"] if c["id"] == chore_id), None)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/chores")
def get_chores():
    return jsonify(load_state())


@app.post("/api/chores")
def add_chore():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip()
    freq = int(body.get("freqDays", 7))
    if not name:
        return jsonify({"error": "name is required"}), 400
    if freq < 1:
        return jsonify({"error": "freqDays must be >= 1"}), 400

    state = load_state()
    new_chore = {
        "id": state["nextId"],
        "name": name,
        "freqDays": freq,
        "lastDone": None,
        "lastBy": None,
        "history": [],
    }
    state["chores"].append(new_chore)
    state["nextId"] += 1
    save_state(state)
    return jsonify(new_chore), 201


@app.delete("/api/chores/<int:chore_id>")
def delete_chore(chore_id: int):
    state = load_state()
    before = len(state["chores"])
    state["chores"] = [c for c in state["chores"] if c["id"] != chore_id]
    if len(state["chores"]) == before:
        return jsonify({"error": "not found"}), 404
    save_state(state)
    return "", 204


@app.post("/api/chores/<int:chore_id>/complete")
def complete_chore(chore_id: int):
    body = request.get_json(silent=True) or {}
    user = str(body.get("user", "")).strip() or "Unknown"

    state = load_state()
    chore = find_chore(state, chore_id)
    if not chore:
        return jsonify({"error": "not found"}), 404

    # Push current state onto history stack (keep last 20 entries)
    chore["history"].append({"ts": chore["lastDone"], "by": chore["lastBy"]})
    chore["history"] = chore["history"][-20:]

    chore["lastDone"] = int(time.time() * 1000)  # ms epoch, same as JS Date.now()
    chore["lastBy"] = user
    save_state(state)
    return jsonify(chore)


@app.post("/api/chores/<int:chore_id>/undo")
def undo_chore(chore_id: int):
    state = load_state()
    chore = find_chore(state, chore_id)
    if not chore:
        return jsonify({"error": "not found"}), 404
    if not chore["history"]:
        return jsonify({"error": "nothing to undo"}), 400

    prev = chore["history"].pop()
    chore["lastDone"] = prev["ts"]
    chore["lastBy"] = prev["by"]
    save_state(state)
    return jsonify(chore)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": int(time.time() * 1000)})


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[chore-tracker] Starting on port {PORT}")
    print(f"[chore-tracker] Data file: {DATA_FILE}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
