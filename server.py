import os
import json
from typing import List
from fastapi import FastAPI, WebSocket, UploadFile, File, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncpg
import asyncio
import uuid
import shutil


app = FastAPI()

# Autoriser toutes les origines pour le LAN
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Liste des clients connectés
clients: List[WebSocket] = []

# Dossier pour fichiers uploadés
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Fichier de stockage des messages
MESSAGES_FILE = "messages.json"

# Charger l'historique depuis le fichier
def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        return []  # pas encore de fichier

    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # fichier vide
                return []
            return json.loads(content)
    except Exception as e:
        print("Erreur lecture messages.json :", e)
        return []  # si corrompu → on renvoie une liste vide

# Sauvegarder un message
def save_message(message):
    messages = load_messages()
    messages.append(message)
    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

# Route pour récupérer l’historique
@app.get("/history")
async def get_history():
    return JSONResponse(load_messages())

# Route WebSocket pour chat texte et fichiers
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            # On attend un JSON {clientId, text, isFile}
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                data = {"clientId": None, "text": data_str, "isFile": False}
            # Sauvegarder le message
            save_message(data)
            # Envoyer à tous les clients
            for client in clients:
                await client.send_text(json.dumps(data))
    except:
        clients.remove(websocket)

# Route upload fichiers (plusieurs fichiers à la fois)
@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        saved_files.append(file.filename)

    return {"filenames": saved_files}

# Servir les fichiers uploadés
@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    return FileResponse(file_path)

# ⚡ Servir les fichiers statiques (index.html, JS, CSS)
app.mount("/", StaticFiles(directory="templates", html=True), name="templates")

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=5000, reload=True)