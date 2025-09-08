import logging
from datetime import datetime, timedelta

import bcrypt
import cv2
import jwt
import numpy as np
import psycopg2.extras
from flask import Blueprint, jsonify, render_template, request
from werkzeug.utils import secure_filename

from config import Config
from modules.database import FaceDatabase
from modules.detector import FaceDetector

admin_bp = Blueprint("admin", __name__)

face_detector = FaceDetector(device="cuda")
face_db = FaceDatabase(
    dbname=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


def generate_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=8)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')


def verify_token(token):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@admin_bp.route('/')
def index():
    return render_template('admin/admin.html')


@admin_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Thiếu username hoặc password'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()

        if admin and bcrypt.checkpw(password.encode("utf-8"), admin['password_hash'].encode("utf-8")):
            token = generate_token(admin['id'], admin['username'])
            conn.close()
            return jsonify({
                'success': True,
                'message': 'Đăng nhập thành công',
                'token': token,
                'user': {'id': admin['id'], 'username': admin['username']}
            })
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Sai username hoặc password'}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Thiếu username hoặc password'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE username = %s", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Username đã tồn tại'}), 400

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username, hashed_pw)
        )
        admin_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Đăng ký thành công', 'id': admin_id}), 201

    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT e.*, COUNT(fe.id) as face_count
            FROM employees e
            LEFT JOIN face_embeddings fe ON e.id = fe.employee_id
            GROUP BY e.id
            ORDER BY e.created_at DESC
        """)
        employees = cursor.fetchall()
        conn.close()

        return jsonify({'success': True, 'data': employees})

    except Exception as e:
        logger.error(f"Get employees error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('/api/employees', methods=['POST'])
def add_employee():
    try:
        employee_code = request.form.get('employee_code')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position = request.form.get('position')

        if not all([employee_code, name, email, phone, position]):
            return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE employee_code = %s", (employee_code,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Mã nhân viên đã tồn tại'}), 400

        cursor.execute("""
            INSERT INTO employees (employee_code, name, email, phone, position)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (employee_code, name, email, phone, position))
        employee_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{employee_code}_{file.filename}")

                file_bytes = file.read()
                np_arr = np.frombuffer(file_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                boxes = face_detector.detect_faces(frame)
                faces = face_detector.extract_faces(frame, boxes)

                if faces:
                    embedding = face_detector.get_embeddings(faces[0])
                    face_db.add_face(employee_id, employee_code, embedding, filename)

        return jsonify({
            'success': True,
            'message': 'Thêm nhân viên thành công',
            'employee_id': employee_id
        })

    except Exception as e:
        logger.error(f"Add employee error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    try:
        data = request.get_json()
        email = data.get('email')
        phone = data.get('phone')
        position = data.get('position')

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees 
            SET email = %s, phone = %s, position = %s
            WHERE id = %s
        """, (email, phone, position, employee_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Cập nhật thành công'})

    except Exception as e:
        logger.error(f"Update employee error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Xóa nhân viên thành công'})

    except Exception as e:
        logger.error(f"Delete employee error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        date_filter = request.args.get('date')
        status_filter = request.args.get('status')

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            SELECT al.id, al.employee_code, e.name AS employee_name,
                   al.check_time, al.check_type, al.work_status
            FROM attendance_logs al
            LEFT JOIN employees e ON al.employee_id = e.id
            WHERE 1=1
        """
        params = []

        if date_filter:
            query += " AND DATE(al.check_time) = %s"
            params.append(date_filter)

        if status_filter:
            query += " AND al.work_status = %s"
            params.append(status_filter)

        query += " ORDER BY al.check_time DESC LIMIT 100"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        data = []
        for r in rows:
            check_time = r['check_time']
            data.append({
                'id': r['id'],
                'employee_code': r['employee_code'],
                'employee_name': r['employee_name'],
                'date': check_time.strftime("%Y-%m-%d") if check_time else None,
                'checkin_time': check_time.strftime("%H:%M") if (check_time and r['check_type'] == 'checkin') else None,
                'checkout_time': check_time.strftime("%H:%M") if (check_time and r['check_type'] == 'checkout') else None,
                'status': r['work_status']
            })

        return jsonify({'success': True, 'data': data})

    except Exception as e:
        logger.error(f"Get attendance error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = cursor.fetchone()[0]

        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(DISTINCT employee_id) 
            FROM attendance_logs 
            WHERE DATE(check_time) = %s AND check_type = 'checkin'
        """, (today,))
        present_today = cursor.fetchone()[0]

        absent_today = total_employees - present_today

        cursor.execute("""
            SELECT COUNT(DISTINCT employee_id) 
            FROM attendance_logs 
            WHERE DATE(check_time) = %s 
            AND check_type = 'checkin' 
            AND EXTRACT(HOUR FROM check_time) > 9
            AND EXTRACT(MINUTE FROM check_time) > 0 
        """, (today,))
        late_today = cursor.fetchone()[0]

        cursor.execute("""
            SELECT al.*, e.name as employee_name
            FROM attendance_logs al
            LEFT JOIN employees e ON al.employee_id = e.id
            ORDER BY al.check_time DESC
            LIMIT 10
        """)
        recent_attendance = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'total_employees': total_employees,
                'present_today': present_today,
                'absent_today': absent_today,
                'late_today': late_today,
                'recent_attendance': [dict(zip([col[0] for col in cursor.description], row)) for row in recent_attendance] if recent_attendance else []
            }
        })

    except Exception as e:
        logger.error(f"Get dashboard stats error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500


@admin_bp.route('ad/api/checkin', methods=['POST'])
def checkin():
    """API chấm công (checkin/checkout)"""
    try:
        data = request.get_json()
        employee_code = data.get('employee_code')
        check_type = data.get('check_type', 'checkin')

        if not employee_code:
            return jsonify({'success': False, 'message': 'Thiếu mã nhân viên'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Lỗi kết nối database'}), 500

        cursor = conn.cursor()

        cursor.execute("SELECT id FROM employees WHERE employee_code = %s", (employee_code,))
        employee = cursor.fetchone()

        if not employee:
            conn.close()
            return jsonify({'success': False, 'message': 'Không tìm thấy nhân viên'}), 404

        employee_id = employee[0]
        current_time = datetime.now()

        work_status = "Có mặt"
        if check_type == 'checkin':
            expected_time = current_time.replace(hour=Config.CHECKIN_HOUR, minute=0)
            if current_time > expected_time + timedelta(minutes=15):
                work_status = "Đi muộn"

        cursor.execute("""
            INSERT INTO attendance_logs (employee_id, employee_code, check_time, check_type, work_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (employee_id, employee_code, current_time, check_type, work_status))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'{check_type.title()} thành công',
            'time': current_time.strftime('%H:%M:%S'),
            'status': work_status
        })

    except Exception as e:
        logger.error(f"Checkin error: {e}")
        return jsonify({'success': False, 'message': 'Lỗi server'}), 500
