from flask import Flask, Blueprint, render_template, jsonify
import os
import json

views = Blueprint('views', __name__)

# Routes
@views.route('/')
@views.route('/home')
def home():
    return render_template('home.html')

@views.route('/login')
def login():
    return render_template('login.html')

@views.route('/register')
def register():
    return render_template('register.html')

@views.route('/chat')
def chat():
    return render_template('chat.html')


@views.route('/admin')
def admin():
    return render_template('admin.html')

# Route pour l'historique des messages (GET /history)
@views.route('/history')
def history():
    messages_file = os.path.join(os.path.dirname(__file__), 'messages.json')
    if not os.path.exists(messages_file):
        return jsonify([])
    try:
        with open(messages_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return jsonify([])
            return jsonify(json.loads(content))
    except Exception as e:
        print('Erreur lecture messages.json :', e)
        return jsonify([])