import base64
from datetime import datetime

import cv2
import numpy as np
import torch
from flask import Blueprint, jsonify, render_template, request

from config import Config
from modules.database import FaceDatabase
from modules.detector import FaceDetector
from modules.livenessnet import LivenessNet
from modules.recognition import FaceRecognizer

user_bp = Blueprint("user", __name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
detector = FaceDetector(device=DEVICE)

liveness_model = LivenessNet(width=32, height=32, depth=3, classes=2)
checkpoint = torch.load(Config.MODEL_PATH, map_location=DEVICE)
liveness_model.load_state_dict(checkpoint["model_state_dict"])
liveness_model.to(DEVICE)
liveness_model.eval()

db = FaceDatabase(
    dbname=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT
)

recognizer = FaceRecognizer(db, threshold=0.7)

def preprocess_for_liveness(face_img):
    img = cv2.resize(face_img, (32, 32))
    img = img.astype("float32") / 255.0
    img = np.transpose(img, (2, 0, 1))
    return torch.tensor(img).unsqueeze(0).to(DEVICE)


def log_attendance(employee_id, employee_code, check_type, image_path=None):
    check_time = datetime.now().replace(microsecond=0)

    if check_type == "checkin":
        status = "present" if check_time.hour <= Config.CHECKIN_HOUR else "late"
    elif check_type == "checkout":
        status = "present" if check_time.hour >= Config.CHECKOUT_HOUR else "early"
    else:
        status = "unknown"

    try:
        cur = db.conn.cursor()

        cur.execute(
            """
            SELECT id FROM attendance_logs
            WHERE employee_id = %s
              AND check_type = %s
              AND check_time::date = CURRENT_DATE
            """,
            (employee_id, check_type)
        )
        if cur.fetchone():
            cur.close()
            return {"success": False, "message": f"Bạn đã {check_type} hôm nay rồi!"}

        cur.execute(
            """
            INSERT INTO attendance_logs (employee_id, employee_code, check_time, check_type, image_path, work_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (employee_id, employee_code, check_time, check_type, image_path, status)
        )
        db.conn.commit()
        cur.close()
        return {"success": True, "message": f"{check_type.capitalize()} thành công!"}

    except Exception as e:
        db.conn.rollback()
        print("Error logging attendance:", e)
        return {"success": False, "message": "Lỗi khi ghi chấm công"}


def get_next_check_type(employee_id):
    try:
        cur = db.conn.cursor()
        cur.execute(
            """
            SELECT check_type
            FROM attendance_logs
            WHERE employee_id = %s AND check_time::date = CURRENT_DATE
            ORDER BY check_time DESC
            LIMIT 1
            """,
            (employee_id,)
        )
        row = cur.fetchone()
        cur.close()
    except Exception as e:
        print("Error fetching last check type:", e)
        row = None

    if not row:
        return "checkin"
    last_type = row[0]
    return "checkout" if last_type == "checkin" else "checkin"


@user_bp.route("/")
def index():
    return render_template("user/user.html")


@user_bp.route("/api/recognize", methods=["POST"])
def recognize():
    data = request.get_json()
    if "image" not in data:
        return jsonify({"status": "error", "message": "No image provided"}), 400

    check_time = datetime.now().strftime("%H:%M")
    img_data = base64.b64decode(data["image"].split(",")[1])
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    boxes = detector.detect_faces(frame)
    if not boxes:
        return jsonify({"status": "no_face", "message": "Không phát hiện khuôn mặt"})

    faces = detector.extract_faces(frame, boxes)
    embeddings = [detector.get_embeddings(face) for face in faces]

    for box, face_img, embedding in zip(boxes, faces, embeddings):
        # 1. Liveness check
        tensor = preprocess_for_liveness(face_img)
        with torch.no_grad():
            output = liveness_model(tensor)
            pred = torch.argmax(output, dim=1).item()
            is_real = (pred == 1)

        if not is_real:
            return jsonify({"status": "fake", "message": "Phát hiện ảnh giả", "name": "FAKE"})

        # 2. Nhận diện gương mặt
        employee_id, employee_code, dist, conf = recognizer.recognize(embedding)

        if employee_code == "Unknown" or employee_id is None:
            return jsonify({"status": "unknown", "message": "Không nhận diện được", "name": "Unknown"})

        # 3. Xác định check_type tự động
        check_type = get_next_check_type(employee_id)

        # 4. Ghi log chấm công
        log_attendance(employee_id, employee_code, check_type, None)

        # 5. Trả kết quả
        return jsonify({
            "status": "ok",
            "employee_code": employee_code,
            "message": f"{check_type} thành công - {check_time}",
            "name": employee_code
        })

    return jsonify({"status": "error", "message": "Không có kết quả"})


