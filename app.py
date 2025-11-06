from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

DB = "bbs.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app = Flask(__name__)
DB = "bbs.db"

# 画像アップロードフォルダを自動作成
os.makedirs("static/uploads", exist_ok=True)

# アップロード設定
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# --- 画像の拡張子チェック ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- データベース初期化 ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board TEXT NOT NULL,
            name TEXT,
            message TEXT NOT NULL,
            image TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

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
    cur.execute("SELECT DISTINCT board FROM posts ORDER BY board;")
    boards = [row["board"] for row in cur.fetchall()]
    conn.close()
    return render_template("boards.html", boards=boards)


# --- 板ページ ---
@app.route("/board/<board>", methods=["GET", "POST"])
def board(board):
    conn = get_db()
    cur = conn.cursor()

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
            cur.execute("INSERT INTO posts (board, name, message, image) VALUES (?, ?, ?, ?)",
                        (board, name, message, image_path))
            conn.commit()

    cur.execute("SELECT * FROM posts WHERE board=? ORDER BY date DESC;", (board,))
    posts = cur.fetchall()
    conn.close()

    return render_template("board.html", board=board, posts=posts)


# --- 新しい板を作る ---
@app.route("/create", methods=["POST"])
def create_board():
    board_name = request.form["board"].strip()
    if board_name:
        return redirect(f"/board/{board_name}")
    return redirect("/")


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

