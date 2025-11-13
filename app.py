from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==============================
# 基本設定
# ==============================
DB_PATH = os.path.join(os.path.dirname(__file__), "bbs.db")
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# ==============================
# DB初期化
# ==============================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 板テーブル
    c.execute("""
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
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
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ✅ Render上でも確実に実行
init_db()


# ==============================
# ヘルパー関数
# ==============================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==============================
# 板一覧ページ
# ==============================
@app.route("/")
def boards():
    conn = get_db()
    boards = conn.execute("SELECT * FROM boards ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("boards.html", boards=boards)


# ==============================
# 板を作成
# ==============================
@app.route("/create_board", methods=["POST"])
def create_board():
    name = request.form["name"].strip()
    description = request.form.get("description", "").strip()

    if name:
        conn = get_db()
        conn.execute("INSERT INTO boards (title, description) VALUES (?, ?)", (name, description))
        conn.commit()
        conn.close()
    return redirect("/")


# ==============================
# 板を削除
# ==============================
@app.route("/delete_board/<int:board_id>", methods=["POST"])
def delete_board(board_id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE board_id=?", (board_id,))
    conn.execute("DELETE FROM boards WHERE id=?", (board_id,))
    conn.commit()
    conn.close()
    return redirect("/")


# ==============================
# 板ページ（投稿一覧＋投稿フォーム）
# ==============================
@app.route("/board/<int:board_id>", methods=["GET", "POST"])
def board(board_id):
    conn = get_db()
    board = conn.execute("SELECT * FROM boards WHERE id=?", (board_id,)).fetchone()

    if not board:
        conn.close()
        return "指定された板が存在しません。", 404

    # 投稿処理
    if request.method == "POST":
        name = request.form.get("name", "名無しさん")
        message = request.form["message"].strip()
        image_path = None

        # 画像アップロード処理
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                image_path = f"{UPLOAD_FOLDER}/{filename}"

        if message:
            conn.execute(
                "INSERT INTO posts (board_id, name, message, image) VALUES (?, ?, ?, ?)",
                (board_id, name, message, image_path),
            )
            conn.commit()

    posts = conn.execute("SELECT * FROM posts WHERE board_id=? ORDER BY date DESC", (board_id,)).fetchall()
    conn.close()

    return render_template("board.html", board=board, posts=posts)


# ==============================
# アプリ起動設定
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

