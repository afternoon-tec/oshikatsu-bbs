from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ===== 設定 =====
DB = "bbs.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ===== DB関連 =====
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    # 板テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 投稿テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL,
            name TEXT,
            message TEXT NOT NULL,
            image TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(board_id) REFERENCES boards(id)
        )
    """)
    conn.commit()
    conn.close()


# ===== 画像ファイル許可チェック =====
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ===== ルーティング =====

# 🏠 板一覧
@app.route("/")
def boards():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM boards ORDER BY created_at DESC;")
    boards = cur.fetchall()
    conn.close()
    return render_template("boards.html", boards=boards)


# ➕ 板作成
@app.route("/create_board", methods=["POST"])
def create_board():
    name = request.form["name"].strip()
    desc = request.form.get("description", "").strip()
    if name:
        conn = get_db()
        conn.execute("INSERT INTO boards (title, description) VALUES (?, ?)", (name, desc))
        conn.commit()
        conn.close()
    return redirect("/")


# ❌ 板削除（投稿もまとめて削除）
@app.route("/delete_board/<int:board_id>", methods=["POST"])
def delete_board(board_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE board_id = ?", (board_id,))
    cur.execute("DELETE FROM boards WHERE id = ?", (board_id,))
    conn.commit()
    conn.close()
    return redirect("/")


# 💬 各板ページ
@app.route("/board/<int:board_id>", methods=["GET", "POST"])
def board(board_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM boards WHERE id = ?", (board_id,))
    board = cur.fetchone()

    if not board:
        conn.close()
        return "この板は存在しません。", 404

    # 投稿処理
    if request.method == "POST":
        name = request.form.get("name", "名無しさん")
        message = request.form["message"]
        image_path = None

        # 画像アップロード
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_path = f"uploads/{filename}"

        if message.strip():
            cur.execute(
                "INSERT INTO posts (board_id, name, message, image) VALUES (?, ?, ?, ?)",
                (board_id, name, message, image_path),
            )
            conn.commit()

    # 投稿一覧
    cur.execute("SELECT * FROM posts WHERE board_id=? ORDER BY date DESC;", (board_id,))
    posts = cur.fetchall()
    conn.close()

    return render_template("board.html", board=board, posts=posts)


# ===== 実行 =====
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

