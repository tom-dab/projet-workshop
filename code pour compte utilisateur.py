from flask import Flask, render_template, request, redirect, session
import psycopg2  # ✅ connecteur PostgreSQL
import bcrypt
import re  # pour la vérification du mot de passe

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- Connexion à la base PostgreSQL ---
def get_db_connection():
    return psycopg2.connect(
        host="https://172.20.101.1:8006",       #  l'adresse de du serv
        database="epsi",
        user="postgres", # identifiant bdd
        password="postgres"      # mot de passe bdd
    )

# ---- PAGE D'INSCRIPTION ----
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # ✅ Vérification de la complexité du mot de passe
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z]).{8,}$', password):
            return "⚠️ Mot de passe trop faible : minimum 8 caractères, une majuscule et une minuscule."

        # Hash du mot de passe
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()

        # Vérifier si le pseudo existe déjà
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            return "⚠️ Ce pseudo existe déjà !"

        # Insertion dans la base
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        return redirect("/login")
 
    return render_template("register.html")

# ---- PAGE DE CONNEXION ----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user[1].encode('utf-8')):
            session["username"] = username
            return f"✅ Bienvenue {username} !"
        else:
            return "❌ Mauvais identifiants."

    return render_template("login.html")

# ---- DÉCONNEXION ----
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug=True)
