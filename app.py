from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# --- Flask 設定 ---
app = Flask(__name__)

# --- PostgreSQL 接続設定 ---
# Render の「Environment Variables」に DATABASE_URL を設定する
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL が設定されていません。Render の環境変数に追加してください。")

# SQLAlchemy 用の接続文字列に変換（sqlite3 対応ではないため）
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL.replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- 画像アップロード設定 ---
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# --- モデル定義 ---
class Board(db.Model):
    __tablename__ = "boards"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship("Post", backref="board", cascade="all, delete")


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey("boards.id"), nullable=False)
    name = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)


# --- 初回自動テーブル作成 ---
with app.app_context():
    db.create_all()


# --- 拡張子チェック ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- 板一覧 ---
@app.route("/")
def boards():
    boards = Board.query.order_by(Board.created_at.desc()).all()
    return render_template("boards.html", boards=boards)


# --- 板作成 ---
@app.route("/create_board", methods=["POST"])
def create_board():
    name = request.form["name"].strip()
    description = request.form.get("description", "")
    if name:
        board = Board(title=name, description=description)
        db.session.add(board)
        db.session.commit()
    return redirect(url_for("boards"))


# --- 板削除 ---
@app.route("/delete_board/<int:board_id>", methods=["POST"])
def delete_board(board_id):
    board = Board.query.get_or_404(board_id)
    db.session.delete(board)
    db.session.commit()
    return redirect(url_for("boards"))


# --- 投稿ページ ---
@app.route("/board/<int:board_id>", methods=["GET", "POST"])
def board(board_id):
    board = Board.query.get_or_404(board_id)

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
                image_path = f"uploads/{filename}"

        if message.strip():
            post = Post(board_id=board.id, name=name, message=message, image=image_path)
            db.session.add(post)
            db.session.commit()

    posts = Post.query.filter_by(board_id=board.id).order_by(Post.date.desc()).all()
    return render_template("board.html", board=board, posts=posts)


# --- Render でのエントリポイント ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
