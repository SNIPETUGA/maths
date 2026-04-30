# Mathos - Flask API with auth

import os

from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "mathos-secret-key"

def connect():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mathos.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def setup():
    conn = connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS favours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            person TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (requester_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = generate_password_hash(data["password"])
    try:
        conn = connect()
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Account created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    conn = connect()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"message": f"Welcome, {username}"}), 200
    return jsonify({"error": "Invalid username or password"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@app.route("/favours", methods=["GET"])
def get_favours():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM favours WHERE user_id = ?", (session["user_id"],)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/favours", methods=["POST"])
def log_favour():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    person = data["person"]
    description = data["description"]
    category = data.get("category", "other")
    today = str(date.today())
    conn = connect()
    conn.execute(
        "INSERT INTO favours (user_id, person, description, date, category) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], person, description, today, category)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Logged favour for {person}"}), 201

@app.route("/favours/<person>", methods=["GET"])
def get_by_person(person):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM favours WHERE user_id = ? AND LOWER(person) = LOWER(?)",
        (session["user_id"], person)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/contacts/request", methods=["POST"])
def send_request():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    username = data["username"]
    conn = connect()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    if user["id"] == session["user_id"]:
        conn.close()
        return jsonify({"error": "You can't add yourself"}), 400
    existing = conn.execute(
        "SELECT * FROM contacts WHERE requester_id = ? AND receiver_id = ?",
        (session["user_id"], user["id"])
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Request already sent"}), 400
    conn.execute(
        "INSERT INTO contacts (requester_id, receiver_id) VALUES (?, ?)",
        (session["user_id"], user["id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Request sent to {username}"}), 201

@app.route("/contacts/pending", methods=["GET"])
def pending_requests():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = connect()
    rows = conn.execute("""
        SELECT contacts.id, users.username
        FROM contacts
        JOIN users ON contacts.requester_id = users.id
        WHERE contacts.receiver_id = ? AND contacts.status = 'pending'
    """, (session["user_id"],)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/contacts/accept/<int:contact_id>", methods=["POST"])
def accept_request(contact_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = connect()
    conn.execute(
        "UPDATE contacts SET status = 'accepted' WHERE id = ? AND receiver_id = ?",
        (contact_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Contact accepted"}), 200

@app.route("/contacts", methods=["GET"])
def get_contacts():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = connect()
    rows = conn.execute("""
        SELECT users.id, users.username
        FROM contacts
        JOIN users ON (
            CASE
                WHEN contacts.requester_id = ? THEN contacts.receiver_id
                ELSE contacts.requester_id
            END
        ) = users.id
        WHERE (contacts.requester_id = ? OR contacts.receiver_id = ?)
        AND contacts.status = 'accepted'
    """, (session["user_id"], session["user_id"], session["user_id"])).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/favours/<int:favour_id>/react", methods=["POST"])
def react_to_favour(favour_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    reaction = data["reaction"]
    if reaction not in ["❤️", "🙏", "😊"]:
        return jsonify({"error": "Invalid reaction"}), 400
    conn = connect()
    conn.execute(
        "UPDATE favours SET reaction = ? WHERE id = ?",
        (reaction, favour_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Reaction added"}), 200

@app.route("/favours/for-me", methods=["GET"])
def favours_for_me():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    conn = connect()
    rows = conn.execute("""
        SELECT favours.*, users.username as logged_by
        FROM favours
        JOIN users ON favours.user_id = users.id
        WHERE LOWER(favours.person) = LOWER(?)
    """, (session["username"],)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

setup()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=5001)