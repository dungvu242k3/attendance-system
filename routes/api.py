import base64
from datetime import datetime

import cv2
import numpy as np
import torch
from flask import Blueprint, jsonify, request

from config import Config
from modules.database import FaceDatabase
from modules.detector import FaceDetector
from modules.livenessnet import LivenessNet
from modules.recognition import FaceRecognizer

api_bp = Blueprint("api", __name__)

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


def log_attendance(employee_id, name, check_type, image_path=None):
    check_time = datetime.now().replace(microsecond=0)
    if check_type == "checkin":
        status = "present" if check_time.hour < Config.CHECKIN_HOUR else "late"
    elif check_type == "checkout":
        status = "present" if check_time.hour < Config.CHECKOUT_HOUR else "late"
    else:
        status = "unknown"
    try:
        cur = db.conn.cursor()
        cur.execute(
            "INSERT INTO attendance_logs_512 (employee_id, person_name, status, check_type, check_time, image_path) VALUES (%s, %s, %s, %s, %s, %s)",
            (employee_id, name, status, check_type, check_time, image_path)
        )
        db.conn.commit()
        cur.close()
    except Exception as e:
        db.conn.rollback()
        print("Error logging attendance:", e)


@api_bp.route("/recognize", methods=["POST"])
def recognize():
    data = request.get_json()
    if "image" not in data:
        return jsonify({"status": "error", "message": "No image provided"}), 400

    check_type = data.get("type", "checkin")
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
        tensor = preprocess_for_liveness(face_img)
        with torch.no_grad():
            output = liveness_model(tensor)
            pred = torch.argmax(output, dim=1).item()
            is_real = (pred == 1)

        if not is_real:
            return jsonify({"status": "fake", "message": "Phát hiện ảnh giả", "name": "FAKE"})

        employee_id, name, dist, conf = recognizer.recognize(embedding)

        if name == "Unknown":
            return jsonify({"status": "unknown", "message": "Không nhận diện được", "name": "Unknown"})

        log_attendance(employee_id, name, check_type, None)

        return jsonify({"status": "ok", "message": f"{check_type} thành công - {check_time}", "name": name})

    return jsonify({"status": "error", "message": "Không có kết quả"})
