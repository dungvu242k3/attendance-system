import datetime

import bcrypt
import jwt
import psycopg2
from flask import Blueprint, jsonify, request

from config import Config

auth_bp = Blueprint("auth", __name__)

def generate_token(admin_id, username):
    payload = {
        "id": admin_id,
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def get_db_conn():
    """Tạo connection mới cho mỗi request"""
    return psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )

# ================= Register =================
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu username hoặc password"}), 400

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM admins WHERE username = %s", (username,))
                if cur.fetchone():
                    return jsonify({"error": "Username đã tồn tại"}), 400

                hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

                cur.execute(
                    "INSERT INTO admins (username, password_hash) VALUES (%s, %s) RETURNING id",
                    (username, hashed_pw)
                )
                admin_id = cur.fetchone()[0]
        return jsonify({"message": "Đăng ký thành công"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Thiếu username hoặc password"}), 400

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password_hash FROM admins WHERE username = %s", (username,))
                row = cur.fetchone()

        if not row:
            return jsonify({"error": "Sai username hoặc password"}), 401

        admin_id, password_hash = row
        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            return jsonify({"error": "Sai username hoặc password"}), 401

        token = generate_token(admin_id, username)
        return jsonify({
            "message": "Đăng nhập thành công",
            "token": token,
            "user": {"id": admin_id, "username": username}
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
