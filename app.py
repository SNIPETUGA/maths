# Mathos - Flask API

from flask import Flask, request, jsonify
import sqlite3
from datetime import date

app = Flask(__name__)

def connect():
    conn = sqlite3.connect("mathos.db")
    conn.row_factory = sqlite3.Row
    return conn

def setup():
    conn = connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS favours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route("/favours", methods=["GET"])
def get_favours():
    conn = connect()
    rows = conn.execute("SELECT * FROM favours").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/favours", methods=["POST"])
def log_favour():
    data = request.get_json()
    person = data["person"]
    description = data["description"]
    today = str(date.today())
    conn = connect()
    conn.execute(
        "INSERT INTO favours (person, description, date) VALUES (?, ?, ?)",
        (person, description, today)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Logged favour for {person}"}), 201

@app.route("/favours/<person>", methods=["GET"])
def get_by_person(person):
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM favours WHERE LOWER(person) = LOWER(?)",
        (person,)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

setup()

if __name__ == "__main__":
    app.run(debug=True)