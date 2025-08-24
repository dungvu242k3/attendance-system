from flask import Blueprint, render_template

from config import Config
from modules.database import FaceDatabase

user_bp = Blueprint("user", __name__)

db = FaceDatabase(
    dbname=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT
)

@user_bp.route("/")
def index():
    """Trang giao diện chính cho nhân viên"""
    return render_template("user/index.html")


@user_bp.route("/history")
def history():
    """Xem lịch sử điểm danh của nhân viên"""
    cur = db.conn.cursor()
    cur.execute("""
        SELECT id, person_name, status, check_time, image_path
        FROM attendance_logs_512
        ORDER BY check_time DESC
    """)
    records = cur.fetchall()
    cur.close()
    return render_template("user/history.html", records=records)
