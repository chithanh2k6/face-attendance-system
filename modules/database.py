import sqlite3
import os

BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
DB_PATH     = os.path.join(DATA_DIR, "attendance.db")
FACES_DIR   = os.path.join(DATA_DIR, "faces")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def initialize_directories():
    """
    tạo các thư mục cần thiết  nếu chưa tồn tại.
    """
    for d in [DATA_DIR, FACES_DIR, REPORTS_DIR]:
        os.makedirs(d, exist_ok=True)


def connect_db(db_path=DB_PATH):
    """
    tự động tạo file DB nếu chưa tồn tại.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Truy cập cột bằng tên: row["student_id"]
    return conn


def create_tables(db_path=DB_PATH):
    """
    Tạo các bảng cần thiết và cấu trúc thư mục nếu chưa tồn tại.
    Gọi hàm này 1 lần khi khởi động app
    """
    initialize_directories()

    conn   = connect_db(db_path)
    cursor = conn.cursor()

    # Bảng students
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT    NOT NULL UNIQUE,
            full_name   TEXT    NOT NULL,
            class_name  TEXT,
            gender      TEXT,
            image_path  TEXT,
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Bảng attendance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            time        TEXT    NOT NULL,
            status      TEXT    DEFAULT 'present',
            subject     TEXT,
            note        TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Khởi tạo thư mục và tạo bảng thành công.")


# ──────────────────────────────────────────────
# CRUD cho bảng students
# ──────────────────────────────────────────────

def check_student_status(student_id, db_path=DB_PATH):
    """
    Hàm chuyên biệt kiểm tra trạng thái sinh viên trong DB.
    Trả về một tuple độc lập: (exists: bool, is_active: bool)
    Giúp bóc tách logic kiểm tra ra khỏi luồng xử lý String phức tạp.
    """
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return False, False  # Không tồn tại
    return True, row["is_active"] == 1


def add_student(student_id, full_name, class_name="", gender="", image_path="", db_path=DB_PATH):
    """
    Thêm sinh viên mới tinh vào DB.
    Hàm tuân thủ nguyên tắc nhất quán dữ liệu, trả về kiểu Boolean thuần túy.
    Trả về: True nếu thêm mới thành công, False nếu trùng khóa UNIQUE.
    """
    try:
        conn = connect_db(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (student_id, full_name, class_name, gender, image_path, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (student_id, full_name, class_name, gender, image_path))
        conn.commit()
        conn.close()
        print(f"[DB] Đã thêm sinh viên mới: {student_id} - {full_name}")
        return True
    except sqlite3.IntegrityError:
        conn.close()
        print(f"[DB] Lỗi trùng lặp dữ liệu cho MSSV: {student_id}")
        return False


def reactivate_student_db(student_id, full_name, class_name="", gender="", db_path=DB_PATH):
    """
    Hàm ép buộc khôi phục sinh viên bị xóa mềm và cập nhật thông tin mới.
    Được gọi sau khi người dùng bấm đồng ý khôi phục trên giao diện.
    """
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students 
        SET full_name = ?, class_name = ?, gender = ?, image_path = '', is_active = 1 
        WHERE student_id = ?
    """, (full_name, class_name, gender, student_id))
    conn.commit()
    conn.close()
    print(f"[DB] Đã khôi phục hoạt động cho MSSV: {student_id}")


def update_student(student_id, full_name, class_name="", gender="", db_path=DB_PATH):
    """
    Cập nhật thông tin sinh viên (Họ tên, Lớp, Giới tính).
    Chỉ cho phép cập nhật khi sinh viên đang tồn tại và hoạt động (is_active = 1).
    Trả về: True nếu cập nhật thành công, False nếu lỗi hoặc không tìm thấy.
    """
    exists, is_active = check_student_status(student_id, db_path)

    if not exists or not is_active:
        print(f"[DB] Lỗi: MSSV '{student_id}' không tồn tại hoặc đã bị xóa mềm.")
        return False

    conn = connect_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
                   UPDATE students
                   SET full_name  = ?,
                       class_name = ?,
                       gender     = ?
                   WHERE student_id = ?
                   """, (full_name, class_name, gender, student_id))

    conn.commit()
    conn.close()
    print(f"[DB] Đã cập nhật thông tin thành công cho MSSV: {student_id}")
    return True


def get_student(student_id, include_deleted=False, db_path=DB_PATH):
    """
    Lấy thông tin 1 sinh viên theo MSSV.
    - include_deleted = False (Mặc định): Chỉ lấy sinh viên đang hoạt động (Dành cho UI/Nhận diện).
    - include_deleted = True: Lấy cả sinh viên đã xóa mềm (Dành cho báo cáo lịch sử điểm danh).
    """
    conn = connect_db(db_path)
    cursor = conn.cursor()

    if include_deleted:
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    else:
        cursor.execute("SELECT * FROM students WHERE student_id = ? AND is_active = 1", (student_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_students(db_path=DB_PATH):
    """
    Lấy danh sách tất cả sinh viên đang hoạt động
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE is_active = 1 ORDER BY student_id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_student_image(student_id, image_path, db_path=DB_PATH):
    """
    Cập nhật đường dẫn ảnh đại diện của sinh viên sau khi chụp xong.
    Được gọi bởi register.py sau khi lưu ảnh và encode thành công.
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET image_path = ? WHERE student_id = ?",
        (image_path, student_id)
    )
    conn.commit()
    conn.close()


def delete_student(student_id, db_path=DB_PATH):
    """
    giữ nguyên toàn bộ lịch sử điểm danh của sinh viên đó phục vụ báo cáo.
    sau khi gọi hàm này, cần xóa encoding trong pkl bằng cách gọi remove_encoding trong rigister.py
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET is_active = 0 WHERE student_id = ? AND is_active = 1", (student_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    if affected:
        print(f"[DB] Đã xóa sinh viên: {student_id}")
        return True
    return False


def hard_delete_student(student_id, db_path=DB_PATH):
    """
    xóa hoàn toàn khỏi cơ sở dữ liệu.
    chỉ dùng để dọn rác giao dịch khi tiến trình chụp ảnh đăng ký bị hủy giữa chừng.
    """
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()


# def student_exists(student_id, db_path=DB_PATH):
#     """Kiểm tra mssv đang hoạt đọng tồn tại trong DB chưa."""
#     sv = get_student(student_id, include_deleted=False, db_path=db_path)
#     return sv is not None


# ──────────────────────────────────────────────
# CRUD cho bảng attendance
# ──────────────────────────────────────────────

def add_attendance(student_id, date, time, status="present", subject="", note="", db_path=DB_PATH):
    """
    Ghi 1 record điểm danh vào DB.
    Không kiểm tra trùng — gọi has_attended_today() trước khi dùng hàm này.
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO attendance (student_id, date, time, status, subject, note)
        VALUES (?, ?, ?, ?, ?, ?)""", (student_id, date, time, status, subject, note))
    conn.commit()
    conn.close()


def has_attended_today(student_id, date, subject="", db_path=DB_PATH):
    """
    Kiểm tra sv đã điểm danh trong ngày này chưa
    Dùng để tránh ghi trùng trong attendance.py.
    Trả về: True nếu đã điểm danh, False nếu chưa.
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    if subject:
        cursor.execute(
            "SELECT id FROM attendance WHERE student_id=? AND date=? AND subject=?",
            (student_id, date, subject)
        )
    else:
        cursor.execute(
            "SELECT id FROM attendance WHERE student_id=? AND date=?",
            (student_id, date)
        )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_attendance_by_date(date, db_path=DB_PATH):
    """
    lấy danh sách điểm danh theo ngày, kèm họ tên và lớp.
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.student_id, s.full_name, s.class_name,
               a.date, a.time, a.status, a.subject, a.note
        FROM   attendance a
        JOIN   students   s ON a.student_id = s.student_id
        WHERE  a.date = ?
        ORDER  BY a.time
    """, (date,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_attendance_by_student(student_id, db_path=DB_PATH):
    """
    lấy toàn bộ lịch sử điểm danh của 1 sinh viên.
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM attendance
        WHERE  student_id = ?
        ORDER  BY date DESC, time DESC
    """, (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_attendance(db_path=DB_PATH):
    """
    lấy toàn bộ lịch sử điểm danh, kèm họ tên và lớp.
    """
    conn   = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.student_id, s.full_name, s.class_name,
               a.date, a.time, a.status, a.subject, a.note
        FROM   attendance a
        JOIN   students   s ON a.student_id = s.student_id
        ORDER  BY a.date DESC, a.time DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]