from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)
DB = "bbs.db"

# データベース接続
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# 初回用：テーブル作成
def init_db():
    if not os.path.exists(DB):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                message TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

# 掲示板トップ
@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "名無しさん")
        message = request.form["message"]
        if message.strip():
            cur.execute("INSERT INTO posts (name, message) VALUES (?, ?)", (name, message))
            conn.commit()

    cur.execute("SELECT * FROM posts ORDER BY date DESC;")
    posts = cur.fetchall()
    conn.close()

    return render_template("index.html", posts=posts)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
