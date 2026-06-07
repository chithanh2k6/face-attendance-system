import csv
import os
from datetime import datetime

from modules.database import (
    create_tables,
    get_all_attendance,
    get_attendance_by_date,
    REPORTS_DIR,
)


# ──────────────────────────────────────────────
# Cấu hình báo cáo
# ──────────────────────────────────────────────

CSV_HEADERS = [
    "MSSV",
    "Họ tên",
    "Lớp",
    "Ngày",
    "Giờ",
    "Trạng thái",
    "Môn học",
    "Ghi chú",
]


# ──────────────────────────────────────────────
# Xử lý tên file báo cáo
# ──────────────────────────────────────────────

def generate_report_filename(prefix="attendance_report"):
    """
    Tạo tên file CSV tự động theo thời gian hiện tại.
    Tránh ghi đè file báo cáo cũ.

    Ví dụ:
        attendance_report_2026-05-27_143022.csv
    """
    current_time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{prefix}_{current_time}.csv"
    return os.path.join(REPORTS_DIR, filename)


def ensure_reports_dir():
    """
    Đảm bảo thư mục reports/ tồn tại trước khi xuất file.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# Xuất dữ liệu ra CSV
# ──────────────────────────────────────────────

def export_records_to_csv(records, output_file):
    """
    Ghi danh sách điểm danh ra file CSV.

    Tham số:
        records: list dict dữ liệu điểm danh.
        output_file: đường dẫn file CSV cần xuất.

    Trả về:
        (True, message) nếu xuất thành công.
        (False, message) nếu không có dữ liệu hoặc lỗi ghi file.
    """
    if not records:
        return False, "Không có dữ liệu điểm danh để xuất báo cáo."

    ensure_reports_dir()

    try:
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

            for row in records:
                writer.writerow([
                    row.get("student_id", ""),
                    row.get("full_name", ""),
                    row.get("class_name", ""),
                    row.get("date", ""),
                    row.get("time", ""),
                    row.get("status", ""),
                    row.get("subject", ""),
                    row.get("note", ""),
                ])

        return True, f"Xuất báo cáo thành công: {output_file}"

    except Exception as e:
        return False, f"Lỗi khi xuất báo cáo: {e}"


def export_all_attendance(output_file=None):
    """
    Xuất toàn bộ lịch sử điểm danh ra CSV.
    """
    create_tables()

    if output_file is None:
        output_file = generate_report_filename("attendance_all")

    records = get_all_attendance()
    return export_records_to_csv(records, output_file)


def export_attendance_by_date(date, output_file=None):
    """
    Xuất danh sách điểm danh theo ngày ra CSV.

    Tham số:
        date: ngày cần xuất theo định dạng YYYY-MM-DD.
    """
    create_tables()

    date = date.strip() if date else ""

    if not date:
        return False, "Ngày xuất báo cáo không hợp lệ."

    if output_file is None:
        output_file = generate_report_filename(f"attendance_{date}")

    records = get_attendance_by_date(date)
    return export_records_to_csv(records, output_file)


# ──────────────────────────────────────────────
# Hàm in dữ liệu ra terminal để test nhanh
# ──────────────────────────────────────────────

def print_report_preview(records):
    """
    In thử dữ liệu báo cáo ra terminal.
    Dùng để kiểm tra trước khi export CSV.
    """
    if not records:
        print("Không có dữ liệu để hiển thị.")
        return

    print("\n=== PREVIEW BÁO CÁO ĐIỂM DANH ===")
    print(f"{'MSSV':<15} {'Họ tên':<25} {'Lớp':<15} {'Ngày':<12} {'Giờ':<10} {'Trạng thái':<12}")

    for row in records:
        print(
            f"{row.get('student_id', ''):<15} "
            f"{row.get('full_name', ''):<25} "
            f"{row.get('class_name', '') or '':<15} "
            f"{row.get('date', ''):<12} "
            f"{row.get('time', ''):<10} "
            f"{row.get('status', ''):<12}"
        )


# ──────────────────────────────────────────────
# Flow test CLI
# ──────────────────────────────────────────────

def report_cli():
    """
    Menu test nhanh report.py bằng terminal.
    Chạy bằng lệnh:
        python -m modules.report
    """
    create_tables()

    while True:
        print("\n=== TEST REPORT ===")
        print("1. Xem preview toàn bộ điểm danh")
        print("2. Xuất toàn bộ điểm danh ra CSV")
        print("3. Xuất điểm danh theo ngày ra CSV")
        print("0. Thoát")

        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            records = get_all_attendance()
            print_report_preview(records)

        elif choice == "2":
            success, message = export_all_attendance()
            print(message)

        elif choice == "3":
            date = input("Nhập ngày cần xuất (YYYY-MM-DD): ").strip()
            success, message = export_attendance_by_date(date)
            print(message)

        elif choice == "0":
            print("Đã thoát.")
            break

        else:
            print("Lựa chọn không hợp lệ.")


# ──────────────────────────────────────────────
# Test khi chạy trực tiếp
# ──────────────────────────────────────────────

if __name__ == "__main__":
    report_cli()