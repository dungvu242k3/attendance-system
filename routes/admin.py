import base64
import os
import uuid
from datetime import datetime

import cv2
import numpy as np
import psycopg2
from flask import (Blueprint, current_app, jsonify, redirect, render_template,
                   request, url_for)

from config import Config
from modules.database import FaceDatabase
from modules.detector import FaceDetector

admin_bp = Blueprint("admin", __name__)

conn = psycopg2.connect(
    dbname=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT,
)
cur = conn.cursor()

detector = FaceDetector(device="cuda")
face_db = FaceDatabase()


@admin_bp.route("/")
def index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
def dashboard():
    try:
        cur.execute("SELECT COUNT(*) FROM employees")
        total_employees = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM attendance_logs_512 WHERE DATE(check_time) = CURRENT_DATE")
        today_logs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM attendance_logs_512 WHERE DATE(check_time) = CURRENT_DATE AND status='late'")
        late_today = cur.fetchone()[0]

        cur.execute("""
            SELECT person_name, check_time, status, check_type
            FROM attendance_logs_512
            ORDER BY check_time DESC
            LIMIT 5
        """)
        recent = cur.fetchall()

        return render_template(
            "admin/dashboard.html",
            total_employees=total_employees,
            today_logs=today_logs,
            late_today=late_today,
            recent=recent,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/employees")
def employees():
    search_name = request.args.get("name", "")
    position = request.args.get("position", "")

    query = "SELECT id, name, email, phone, position, created_at FROM employees WHERE name LIKE %s"
    params = [f"%{search_name}%"]

    if position:
        query += " AND position = %s"
        params.append(position)

    query += " ORDER BY created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()

    cur.execute("SELECT DISTINCT position FROM employees")
    positions = [r[0] for r in cur.fetchall()]

    return render_template(
        "admin/employees.html",
        employees=rows,
        positions=positions,
        search_name=search_name,
        filter_position=position,
    )


def process_single_image(image_bytes, employee_id, name, image_index=0, filename_prefix=""):
    """
    Xử lý một ảnh duy nhất và trích xuất embedding
    Returns: (success, message, embedding_data)
    """
    try:
        file_np = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(file_np, cv2.IMREAD_COLOR)
        if img is None:
            return False, f"Ảnh {image_index + 1} không hợp lệ", None

        boxes = detector.detect_faces(img)
        if not boxes:
            return False, f"Không phát hiện khuôn mặt trong ảnh {image_index + 1}", None
        
        if len(boxes) > 1:
            print(f"Warning: Phát hiện {len(boxes)} khuôn mặt trong ảnh {image_index + 1}, chỉ lấy khuôn mặt đầu tiên")

        x1, y1, x2, y2 = boxes[0]
        x1, y1 = max(int(x1), 0), max(int(y1), 0)
        x2, y2 = max(int(x2), x1 + 1), max(int(y2), y1 + 1)
        face_img = img[y1:y2, x1:x2]

        embedding = detector.get_embeddings(face_img)
        if isinstance(embedding, np.ndarray):
            embedding_np = embedding.astype(np.float32)
        else:
            embedding_np = embedding.cpu().numpy().astype(np.float32)

        embedding_str = "[" + ",".join(map(str, embedding_np)) + "]"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{employee_id}_{timestamp}_{image_index}.jpg"

        return True, "OK", {
            'embedding': embedding_str,
            'filename': filename
        }

    except Exception as e:
        return False, f"Lỗi xử lý ảnh {image_index + 1}: {str(e)}", None


@admin_bp.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "GET":
        return render_template("admin/add_employee.html")

    try:
        name = (request.form.get("name") or "").strip()
        email = request.form.get("email")
        phone = request.form.get("phone")
        position = request.form.get("position")

        if not name:
            return jsonify({"status": "error", "message": "Tên nhân viên là bắt buộc"}), 400

        MAX_BYTES = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
        
        all_image_data = []
        
        face_images = request.files.getlist('face_images')
        for i, file in enumerate(face_images):
            if file and getattr(file, "filename", ""):
                file_bytes = file.read()
                if len(file_bytes) > MAX_BYTES:
                    return jsonify({
                        "status": "error", 
                        "message": f"File ảnh {i+1} vượt quá {MAX_BYTES//(1024*1024)}MB!"
                    }), 413
                
                all_image_data.append({
                    'data': file_bytes,
                    'source': 'file',
                    'filename': file.filename
                })

        single_file = request.files.get("face_image")
        if single_file and getattr(single_file, "filename", ""):
            file_bytes = single_file.read()
            if len(file_bytes) > MAX_BYTES:
                return jsonify({
                    "status": "error", 
                    "message": f"File ảnh vượt quá {MAX_BYTES//(1024*1024)}MB!"
                }), 413
            
            all_image_data.append({
                'data': file_bytes,
                'source': 'file',
                'filename': single_file.filename
            })

        img_data = request.form.get("face_image_webcam")
        if img_data and img_data.startswith("data:image"):
            header, encoded = img_data.split(",", 1)
            try:
                image_bytes = base64.b64decode(encoded)
                if len(image_bytes) > MAX_BYTES:
                    return jsonify({
                        "status": "error", 
                        "message": f"Ảnh webcam vượt quá {MAX_BYTES//(1024*1024)}MB!"
                    }), 413
                
                all_image_data.append({
                    'data': image_bytes,
                    'source': 'webcam',
                    'filename': 'webcam_capture.jpg'
                })
            except Exception:
                return jsonify({
                    "status": "error", 
                    "message": "Dữ liệu ảnh webcam không hợp lệ"
                }), 400

        if not all_image_data:
            return jsonify({
                "status": "error", 
                "message": "Vui lòng chọn ít nhất một ảnh cho nhân viên"
            }), 400

        cur.execute(
            "INSERT INTO employees (name, email, phone, position) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, email, phone, position),
        )
        employee_id = cur.fetchone()[0]

        successful_embeddings = 0
        failed_images = []
        
        for i, image_info in enumerate(all_image_data):
            success, message, embedding_data = process_single_image(
                image_info['data'], 
                employee_id, 
                name, 
                i, 
                image_info['source']
            )
            
            if success:
                cur.execute(
                    """
                    INSERT INTO face_embeddings_512 (employee_id, person_name, embedding, filename)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (employee_id, name, embedding_data['embedding'], embedding_data['filename']),
                )
                successful_embeddings += 1
            else:
                failed_images.append(f"Ảnh {i+1}: {message}")

        if successful_embeddings == 0:
            cur.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
            conn.rollback()
            error_msg = "Không thể xử lý ảnh nào. Chi tiết:\n" + "\n".join(failed_images)
            return jsonify({"status": "error", "message": error_msg}), 400

        conn.commit()

        response_msg = f"Thêm nhân viên thành công với {successful_embeddings} ảnh"
        if failed_images:
            response_msg += f". Một số ảnh không xử lý được:\n" + "\n".join(failed_images)

        return jsonify({
            "status": "ok",
            "message": response_msg,
            "employee_id": employee_id,
            "total_images": len(all_image_data),
            "successful_embeddings": successful_embeddings,
            "failed_images": len(failed_images)
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Lỗi hệ thống: {str(e)}"}), 500


@admin_bp.route("/edit_employee/<int:emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        position = request.form.get("position")
        try:
            cur.execute(
                """
                UPDATE employees
                SET name=%s, email=%s, phone=%s, position=%s
                WHERE id=%s
                """,
                (name, email, phone, position, emp_id),
            )
            conn.commit()
            return jsonify({"success": True, "message": "Cập nhật thành công"})
        except Exception as e:
            conn.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    cur.execute("SELECT id, name, email, phone, position, created_at FROM employees WHERE id=%s", (emp_id,))
    employee = cur.fetchone()
    return render_template("admin/edit_employee.html", employee=employee)


@admin_bp.route("/delete_employee/<int:emp_id>", methods=["POST"])
def delete_employee(emp_id):
    try:
        cur.execute("DELETE FROM face_embeddings_512 WHERE employee_id = %s", (emp_id,))
        cur.execute("DELETE FROM employees WHERE id = %s RETURNING id", (emp_id,))
        deleted = cur.fetchone()
        if deleted is None:
            conn.rollback()
            return jsonify({"success": False, "message": "Nhân viên không tồn tại"}), 404
        conn.commit()
        return jsonify({"success": True, "message": "Đã xoá nhân viên!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/employee_faces/<int:emp_id>")
def employee_faces(emp_id):
    """
    API endpoint để xem tất cả ảnh/embeddings của một nhân viên
    """
    try:
        cur.execute("SELECT id, name, email, phone, position FROM employees WHERE id=%s", (emp_id,))
        employee = cur.fetchone()
        
        if not employee:
            return jsonify({"error": "Nhân viên không tồn tại"}), 404
        
        cur.execute("""
            SELECT id, filename, created_at 
            FROM face_embeddings_512 
            WHERE employee_id = %s 
            ORDER BY created_at DESC
        """, (emp_id,))
        
        face_embeddings = cur.fetchall()
        
        return jsonify({
            "employee": {
                "id": employee[0],
                "name": employee[1],
                "email": employee[2],
                "phone": employee[3],
                "position": employee[4]
            },
            "face_count": len(face_embeddings),
            "faces": [
                {
                    "id": face[0],
                    "filename": face[1],
                    "created_at": face[2].isoformat() if face[2] else None
                }
                for face in face_embeddings
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/attendance_history")
def attendance_history():
    check_type = request.args.get("type")
    search_name = request.args.get("name", "")
    try:
        query = """
            SELECT id, employee_id, person_name, check_time, status, image_path, check_type
            FROM attendance_logs_512
            WHERE person_name LIKE %s
        """
        params = [f"%{search_name}%"]
        if check_type in ("checkin", "checkout"):
            query += " AND check_type = %s"
            params.append(check_type)
        query += " ORDER BY check_time DESC LIMIT 200"

        cur.execute(query, params)
        rows = cur.fetchall()
        return render_template("admin/history.html", logs=rows)
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500