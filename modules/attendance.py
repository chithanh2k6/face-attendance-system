from datetime import datetime

from modules.database import (
    create_tables,
    get_student,
    add_attendance,
    has_attended_today,
    get_attendance_by_date,
    get_attendance_by_student,
)


# ──────────────────────────────────────────────
# Xử lý ngày giờ
# ──────────────────────────────────────────────

def get_current_date_time():
    """
    Lấy ngày và giờ hiện tại theo định dạng chuẩn để lưu vào DB.
    Trả về tuple: (date, time)
        - date: YYYY-MM-DD
        - time: HH:MM:SS
    """
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    return current_date, current_time


# ──────────────────────────────────────────────
# Logic điểm danh
# ──────────────────────────────────────────────

def mark_attendance(student_id, subject="", note=""):
    """
    Ghi điểm danh cho sinh viên.

    Luồng xử lý:
        1. Kiểm tra MSSV hợp lệ.
        2. Kiểm tra sinh viên có tồn tại và đang hoạt động không.
        3. Kiểm tra sinh viên đã điểm danh trong ngày/môn đó chưa.
        4. Nếu chưa, ghi record vào bảng attendance.

    Trả về:
        (True, message)  nếu điểm danh thành công.
        (False, message) nếu thất bại hoặc đã điểm danh.
    """
    create_tables()

    student_id = student_id.strip() if student_id else ""
    subject = subject.strip() if subject else ""
    note = note.strip() if note else ""

    if not student_id:
        return False, "MSSV không hợp lệ."

    student = get_student(student_id)

    if not student:
        return False, f"Sinh viên '{student_id}' không tồn tại hoặc đã bị xoá."

    current_date, current_time = get_current_date_time()

    if has_attended_today(student_id, current_date, subject):
        return False, f"{student['full_name']} đã điểm danh hôm nay."

    success = add_attendance(
        student_id=student_id,
        date=current_date,
        time=current_time,
        status="present",
        subject=subject,
        note=note,
    )

    if success:
        return True, f"Đã điểm danh: {student['full_name']} ({student_id}) lúc {current_time}"

    return False, "Không thể ghi điểm danh. Có thể dữ liệu đã bị trùng."


# ──────────────────────────────────────────────
# Truy vấn dữ liệu điểm danh
# ──────────────────────────────────────────────

def get_today_attendance():
    """
    Lấy danh sách điểm danh của ngày hiện tại.
    Dùng cho UI, report hoặc test CLI.
    """
    current_date, _ = get_current_date_time()
    return get_attendance_by_date(current_date)


def get_student_attendance_history(student_id):
    """
    Lấy lịch sử điểm danh của 1 sinh viên theo MSSV.
    """
    student_id = student_id.strip() if student_id else ""

    if not student_id:
        return []

    return get_attendance_by_student(student_id)


# ──────────────────────────────────────────────
# Hàm in dữ liệu ra terminal để test nhanh
# ──────────────────────────────────────────────

def print_today_attendance():
    """
    In danh sách điểm danh hôm nay ra terminal.
    Dùng để test độc lập attendance.py.
    """
    records = get_today_attendance()

    if not records:
        print("Hôm nay chưa có sinh viên nào điểm danh.")
        return

    print("\n=== DANH SÁCH ĐIỂM DANH HÔM NAY ===")
    print(f"{'MSSV':<15} {'Họ tên':<25} {'Lớp':<15} {'Ngày':<12} {'Giờ':<10}")

    for row in records:
        print(
            f"{row['student_id']:<15} "
            f"{row['full_name']:<25} "
            f"{row['class_name'] or '':<15} "
            f"{row['date']:<12} "
            f"{row['time']:<10}"
        )


def print_student_attendance_history(student_id):
    """
    In lịch sử điểm danh của 1 sinh viên ra terminal.
    """
    records = get_student_attendance_history(student_id)

    if not records:
        print(f"Không có lịch sử điểm danh cho MSSV: {student_id}")
        return

    print(f"\n=== LỊCH SỬ ĐIỂM DANH: {student_id} ===")
    print(f"{'Ngày':<12} {'Giờ':<10} {'Trạng thái':<12} {'Môn':<15} {'Ghi chú'}")

    for row in records:
        print(
            f"{row['date']:<12} "
            f"{row['time']:<10} "
            f"{row['status']:<12} "
            f"{row['subject'] or '':<15} "
            f"{row['note'] or ''}"
        )


# ──────────────────────────────────────────────
# Flow test CLI
# ──────────────────────────────────────────────

def attendance_cli():
    """
    Menu test nhanh chức năng điểm danh bằng terminal.
    Chạy bằng lệnh:
        python -m modules.attendance
    """
    create_tables()

    while True:
        print("\n=== TEST ATTENDANCE ===")
        print("1. Ghi điểm danh theo MSSV")
        print("2. Xem danh sách điểm danh hôm nay")
        print("3. Xem lịch sử điểm danh của sinh viên")
        print("0. Thoát")

        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            student_id = input("Nhập MSSV: ").strip()
            subject = input("Nhập môn học/lớp học phần (có thể bỏ trống): ").strip()

            success, message = mark_attendance(student_id, subject)
            print(message)

        elif choice == "2":
            print_today_attendance()

        elif choice == "3":
            student_id = input("Nhập MSSV: ").strip()
            print_student_attendance_history(student_id)

        elif choice == "0":
            print("Đã thoát.")
            break

        else:
            print("Lựa chọn không hợp lệ.")


# ──────────────────────────────────────────────
# Test khi chạy trực tiếp
# ──────────────────────────────────────────────

if __name__ == "__main__":
    attendance_cli()