
# --- FLASK VERSION ---
import os
import json
from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
import psycopg
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- DATABASE (PostgreSQL) ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "epsi")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

_db_conn = None

def get_db_connection():
    global _db_conn
    if _db_conn is None or _db_conn.closed:
        _db_conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True,
        )
    return _db_conn

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MESSAGES_FILE = "messages.json"  # conservé pour compat, non utilisé si DB dispo

def load_messages():
    # Lecture depuis la table existante "chats"
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT contenu, fichier FROM chats ORDER BY id ASC"
            )
            rows = cur.fetchall()
            result = []
            for contenu, fichier in rows:
                if fichier:
                    # Si la DB contient déjà une URL absolue, la renvoyer telle quelle
                    if "://" in fichier:
                        url = fichier
                    else:
                        # compat: si un simple nom de fichier est stocké, renvoyer un chemin relatif
                        url = f"/files/{fichier}"
                    result.append({"clientId": None, "text": url, "isFile": True})
                else:
                    result.append({"clientId": None, "text": contenu, "isFile": False})
            return result
    except Exception as e:
        # Fallback fichier si la DB n'est pas joignable
        print("DB non disponible, fallback fichier :", e)
        if not os.path.exists(MESSAGES_FILE):
            return []
        try:
            with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as fe:
            print("Erreur lecture messages.json :", fe)
            return []

def save_message(message):
    # Ecriture dans la table existante "chats"
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            contenu = str(message.get("text") or "")
            is_file = bool(message.get("isFile", False))
            fichier = None
            if is_file:
                # Stocker une valeur téléchargeable en base
                text_val = str(contenu)
                if text_val.startswith("http://") or text_val.startswith("https://"):
                    fichier = text_val  # déjà une URL
                else:
                    # construire une URL absolue vers le fichier servi
                    fichier = f"{BASE_URL}/files/{os.path.basename(text_val)}"
                contenu = ""
            # auteur_id laissé NULL par défaut (pas encore de session utilisateur)
            cur.execute(
                "INSERT INTO chats (auteur_id, contenu, fichier) VALUES (%s, %s, %s)",
                (None, contenu, fichier),
            )
        return
    except Exception as e:
        print("DB non disponible, fallback fichier :", e)
        try:
            messages = []
            if os.path.exists(MESSAGES_FILE):
                with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        messages = json.loads(content)
            messages.append(message)
            with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as fe:
            print("Erreur ecriture messages.json :", fe)


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