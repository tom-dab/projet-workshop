
# --- FLASK VERSION ---
import os
import json
from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MESSAGES_FILE = "messages.json"

def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return []
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception as e:
        print("Erreur lecture messages.json :", e)
        return []

def save_message(message):
    messages = load_messages()
    messages.append(message)
    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


# --- ROUTES WEB (depuis views.py) ---
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

# Route pour l’historique des messages (GET /history)
@app.route("/history", methods=["GET"])
def get_history():
    return jsonify(load_messages())

# Route upload fichiers (plusieurs fichiers à la fois)
@app.route("/upload/", methods=["POST"])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    files = request.files.getlist("files")
    saved_files = []
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        saved_files.append(filename)
    return jsonify({"filenames": saved_files})

# Servir les fichiers uploadés
@app.route("/files/<path:filename>", methods=["GET"])
def get_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)

# Servir les fichiers statiques (JS, CSS, images...)
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# WebSocket pour chat texte et fichiers
@socketio.on("message")
def handle_message(data_str):
    # On attend un JSON {clientId, text, isFile}
    try:
        data = json.loads(data_str) if isinstance(data_str, str) else data_str
    except Exception:
        data = {"clientId": None, "text": str(data_str), "isFile": False}
    save_message(data)
    emit("message", data, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)