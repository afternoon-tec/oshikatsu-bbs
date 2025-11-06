from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# --- Flask設定 ---
app = Flask(__name__)

DB = "bbs.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# 画像フォルダを自動作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# --- 拡張子チェック ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- データベース初期化 ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # 板テーブル
    c.execute("""
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 投稿テーブル
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL,
            name TEXT,
            message TEXT NOT NULL,
            image TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(board_id) REFERENCES boards(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# --- DB接続 ---
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# --- 板一覧 ---
@app.route("/")
def boards():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM boards ORDER BY created_at DESC;")
    boards = cur.fetchall()
    conn.close()
    return render_template("boards.html", boards=boards)


# --- 新しい板を作る ---
@app.route("/create_board", methods=["POST"])
def create_board():
    name = request.form["name"].strip()
    description = request.form.get("description", "")
    if name:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO boards (title, description) VALUES (?, ?)", (name, description))
        conn.commit()
        conn.close()
    return redirect("/")


# --- 板を削除する ---
@app.route("/delete_board/<int:board_id>", methods=["POST"])
def delete_board(board_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE board_id = ?", (board_id,))
    cur.execute("DELETE FROM boards WHERE id = ?", (board_id,))
    conn.commit()
    conn.close()
    return redirect("/")


# --- 各板ページ ---
@app.route("/board/<int:board_id>", methods=["GET", "POST"])
def board(board_id):
    conn = get_db()
    cur = conn.cursor()

    # 投稿処理
    if request.method == "POST":
        name = request.form.get("name", "名無しさん")
        message = request.form["message"]
        image_path = None

        # 画像アップロード処理
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)
                image_path = f"{UPLOAD_FOLDER}/{filename}"

        if message.strip():
            cur.execute("INSERT INTO posts (board_id, name, message, image) VALUES (?, ?, ?, ?)",
                        (board_id, name, message, image_path))
            conn.commit()

    # 板情報と投稿を取得
    cur.execute("SELECT * FROM boards WHERE id = ?", (board_id,))
    board = cur.fetchone()

    cur.execute("SELECT * FROM posts WHERE board_id = ? ORDER BY date DESC;", (board_id,))
    posts = cur.fetchall()

    conn.close()
    return render_template("board.html", board=board, posts=posts)


# --- 起動 ---
if __name__ == "__main__":
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

