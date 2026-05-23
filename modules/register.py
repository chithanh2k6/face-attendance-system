import os
import cv2
import pickle
import shutil
import numpy as np
import face_recognition

from modules.database import (
    create_tables,
    add_student,
    reactivate_student_db,
    check_student_status,
    update_student_image,
    # student_exists,
    delete_student,
    hard_delete_student,
    FACES_DIR,
    DATA_DIR,
)

# ──────────────────────────────────────────────
# Cấu hình
# ──────────────────────────────────────────────

ENCODINGS_FILE = os.path.join(DATA_DIR, "encodings.pkl")
NUM_PHOTOS     = 3  # Số ảnh chụp mỗi sinh viên


# ──────────────────────────────────────────────
# Quản lý file encodings.pkl
# ──────────────────────────────────────────────

def load_encodings():
    """
    Load toàn bộ face encodings từ file .pkl lên RAM.
    Trả về: dict { student_id: numpy array (128,) }
    Nếu file chưa tồn tại → trả về dict rỗng.
    """
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def save_encodings(encodings_dict):
    """
    Lưu toàn bộ dict encodings xuống file .pkl.
    """
    os.makedirs(os.path.dirname(ENCODINGS_FILE), exist_ok=True)
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(encodings_dict, f)

def remove_encoding(student_id):
    """
    Xóa encoding của 1 SV khỏi file .pkl.
    Gọi khi xóa SV để SV đã xóa không bị nhận diện nữa.
    Gọi bởi: UI khi xóa sinh viên (delete_student + remove_encoding)
    """
    all_encodings = load_encodings()
    if student_id in all_encodings:
        del all_encodings[student_id]
        save_encodings(all_encodings)
        print(f"[Encoding] Đã xóa encoding của: {student_id}")


# ──────────────────────────────────────────────
# Hàm dọn rác cho delete
# ──────────────────────────────────────────────

def cleanup_failed_registration(student_id, is_new_student):
    """
    Nhận diện trực tiếp qua cờ tham số `is_new_student`
    - is_new_student = True: Xóa cứng vĩnh viễn khỏi DB (bản ghi rác).
    - is_new_student = False: Trả sinh viên về trạng thái xóa mềm (bảo toàn lịch sử cũ).
    """
    if is_new_student:
        hard_delete_student(student_id)
    else:
        delete_student(student_id)

    student_face_dir = os.path.join(FACES_DIR, student_id)
    if os.path.exists(student_face_dir):
        shutil.rmtree(student_face_dir, ignore_errors=True)


# ──────────────────────────────────────────────
# Nhập thông tin sinh viên (CLI)
# ──────────────────────────────────────────────

def input_student_info():
    """
    Nhập thông tin sinh viên từ bàn phím (Dùng cho test CLI).
    Áp dụng hàm kiểm tra trạng thái độc lập chuyên biệt.
    """
    print("\n=== ĐĂNG KÝ SINH VIÊN MỚI ===")
    student_id = input("Nhập MSSV (để trống để huỷ): ").strip()
    if not student_id:
        return None

    exists, is_active = check_student_status(student_id)

    if exists and is_active:
        print(f"[!] MSSV '{student_id}' đã tồn tại và đang hoạt động.")
        return None

    elif exists and not is_active:
        print(f"\n[?] PHÁT HIỆN: MSSV '{student_id}' từng bị xóa (xóa mềm) trước đây.")
        choice = input("Bạn có muốn khôi phục và cập nhật lại thông tin mới không? (Y/N): ").strip().lower()
        if choice != 'y':
            print("Đã hủy luồng khôi phục.")
            return None
        print("-> Đã đồng ý khôi phục. Vui lòng nhập thông tin mới:")

    full_name = input("Nhập họ và tên đầy đủ: ").strip()
    class_name = input("Nhập tên lớp (VD: CNTT01): ").strip()
    gender = input("Nhập giới tính (Nam/Nữ): ").strip()

    if not full_name:
        print("[!] Họ tên không được để trống.")
        return None

    if exists and not is_active:
        reactivate_student_db(student_id, full_name, class_name, gender)
    else:
        add_student(student_id, full_name, class_name, gender, "")

    return student_id, full_name, class_name, gender, not exists


# ──────────────────────────────────────────────
# Chụp ảnh qua webcam
# ──────────────────────────────────────────────

def capture_face(student_id, num_photos=NUM_PHOTOS):
    """
    Mở webcam, chụp ảnh khuôn mặt sinh viên và lưu vào data/faces/MSSV/
    - Nhấn SPACE để chụp (chỉ khi detect được đúng 1 khuôn mặt)
    - Nhấn Q hoặc bấm X để huỷ
    """
    os.makedirs(FACES_DIR, exist_ok=True)
    student_face_dir = os.path.join(FACES_DIR, student_id)
    os.makedirs(student_face_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Không mở được webcam. Kiểm tra kết nối camera.")
        return []

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    saved_paths  = []
    face_count   = 0
    frame_count  = 0
    DETECT_EVERY = 2

    window_name = f"Camera Dang Ky - {student_id}"
    cv2.namedWindow(window_name)

    while len(saved_paths) < num_photos:
        ret, frame = cap.read()
        if not ret:
            print("[!] Không đọc được frame từ webcam.")
            break

        frame_count += 1

        # Detect khuôn mặt ngầm để giảm lag
        if frame_count % DETECT_EVERY == 0:
            rgb_frame  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locs  = face_recognition.face_locations(rgb_frame, number_of_times_to_upsample=1, model="hog")
            face_count = len(face_locs)

        display = frame.copy()

        if face_count == 1:
            cv2.putText(display, f"SAN SANG ({len(saved_paths)}/{num_photos})", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        else:
            cv2.putText(display, "KHONG THAY MAT", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        cv2.putText(display, "Phim SPACE: Chup | Phim Q: Huy", (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow(window_name, display)
        key = cv2.waitKey(1) & 0xFF

        # Nếu đóng cửa sổ ngang -> Hủy tiến trình
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            saved_paths = []
            break

        if key == ord(' '):
            if face_count == 1:
                img_path = os.path.join(student_face_dir, f"{len(saved_paths)}.jpg")
                cv2.imwrite(img_path, frame)
                saved_paths.append(img_path)
                print(f"[Camera] Da chup {len(saved_paths)}/{num_photos}")

        elif key in (ord('q'), ord('Q')):
            saved_paths = []
            break

    cap.release()
    cv2.destroyAllWindows()
    return saved_paths


# ──────────────────────────────────────────────
# Trích xuất encoding & lưu vào .pkl
# ──────────────────────────────────────────────

def encode_and_save(student_id, image_paths):
    """
    Trích xuất face encoding từ danh sách ảnh đã chụp,
    tính trung bình các vector, lưu vào encodings.pkl.
    Luồng xử lý:
        ảnh JPG → face_recognition → numpy array (128,) → pickle.dump() → .pkl
    """
    encodings = []
    for img_path in image_paths:
        try:
            img  = face_recognition.load_image_file(img_path)
            locs = face_recognition.face_locations(img)
            # num_jitters=5: xử lý ảnh nhiều lần → vector chuẩn xác, triệt tiêu sai số
            enc  = face_recognition.face_encodings(img, known_face_locations=locs, num_jitters=5)
            if enc:
                encodings.append(enc[0])
        except Exception as e:
            print(f"[Encode] Lỗi: {e}")

    if not encodings:
        return False

    avg_encoding = np.mean(encodings, axis=0)
    all_encodings = load_encodings()
    all_encodings[student_id] = avg_encoding
    save_encodings(all_encodings)
    return True


# ──────────────────────────────────────────────
# Flow đăng ký hoàn chỉnh — dùng cho CLI
# ──────────────────────────────────────────────

def register_student_cli():
    """Chạy toàn bộ flow đăng ký từ terminal. Dùng để test độc lập."""
    create_tables()
    info = input_student_info()
    if not info:
        return False

    # Giải nén 5 biến (có is_new_student)
    student_id, full_name, class_name, gender, is_new_student = info

    image_paths = capture_face(student_id)
    if not image_paths or len(image_paths) < NUM_PHOTOS:
        print("[!] Huỷ bỏ hoặc thiếu ảnh. Đang dọn dẹp...")
        cleanup_failed_registration(student_id, is_new_student)
        return False

    if not encode_and_save(student_id, image_paths):
        print("[!] Trích xuất khuôn mặt thất bại. Đang dọn dẹp...")
        cleanup_failed_registration(student_id, is_new_student)
        return False

    update_student_image(student_id, image_paths[0])
    print(f"\n✅ Đăng ký/Khôi phục thành công: {student_id} - {full_name} - {gender}")
    return True


# ──────────────────────────────────────────────
# Flow đăng ký hoàn chỉnh — dùng cho UI
# ──────────────────────────────────────────────

def register_student_from_ui(student_id, full_name, class_name, gender, force_recover=False):
    """
    Tham số mở rộng:
        force_recover = True nếu Người dùng bấm nút [Có] trên Pop-up hỏi ý kiến khôi phục.

    Trả về một tuple gồm 2 thành phần: (status_code, message)
    Các status_code trả về để UI xử lý:
        - "EXISTS"        : MSSV đang hoạt động, chặn đăng ký.
        - "PROMPT_RECOVER": Phát hiện MSSV bị xóa mềm, UI cần hiện hộp thoại hỏi Có/Không.
        - "SUCCESS"       : Đăng ký / Khôi phục thành công mỹ mãn.
        - "FAILED"        : Thất bại do hủy cam hoặc lỗi trích xuất khuôn mặt.
    """
    create_tables()

    # Xác thực dữ liệu rỗng chống crash
    if not full_name or not full_name.strip():
        return "FAILED", "Họ tên không được để trống."
    if not student_id or not student_id.strip():
        return "FAILED", "Mã số sinh viên không được để trống."

    exists, is_active = check_student_status(student_id)
    is_new_student = not exists

    if exists and is_active:
        return "EXISTS", f"MSSV '{student_id}' đang hoạt động trong hệ thống!"

    elif exists and not is_active:
        if not force_recover:
            return "PROMPT_RECOVER", f"Phát hiện MSSV '{student_id}' từng bị xóa trước đây. Bạn có muốn tiến hành khôi phục và cập nhật lại thông tin mới không?"
        else:
            reactivate_student_db(student_id, full_name, class_name, gender)
    else:
        add_student(student_id, full_name, class_name, gender, "")

    image_paths = capture_face(student_id)
    if not image_paths or len(image_paths) < NUM_PHOTOS:
        cleanup_failed_registration(student_id, is_new_student)
        return "FAILED", "Chưa chụp đủ ảnh hoặc đã huỷ camera. Tiến trình bị huỷ."

    if not encode_and_save(student_id, image_paths):
        cleanup_failed_registration(student_id, is_new_student)
        return "FAILED", "Không trích xuất được khuôn mặt. Vui lòng thử lại với ánh sáng tốt hơn."

    update_student_image(student_id, image_paths[0])
    return "SUCCESS", f"Đăng ký thành công sinh viên: {full_name} ({student_id})"


# ──────────────────────────────────────────────
# Test khi chạy trực tiếp
# ──────────────────────────────────────────────

if __name__ == "__main__":
    create_tables()
    register_student_cli()