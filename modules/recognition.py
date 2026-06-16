import cv2
import numpy as np
import face_recognition

from modules.database import create_tables, get_student
from modules.register import load_encodings
from modules.attendance import mark_attendance


# ──────────────────────────────────────────────
# Cấu hình nhận diện
# ──────────────────────────────────────────────

TOLERANCE = 0.5
FRAME_RESIZE_SCALE = 0.25
DETECT_EVERY = 2


# ──────────────────────────────────────────────
# Load dữ liệu khuôn mặt đã đăng ký
# ──────────────────────────────────────────────

def get_known_face_data():
    """
    Load dữ liệu encoding từ encodings.pkl.

    Trả về:
        known_student_ids: list MSSV
        known_face_encodings: list numpy array encoding
    """
    known_encodings = load_encodings()

    if not known_encodings:
        return [], []

    known_student_ids = list(known_encodings.keys())
    known_face_encodings = list(known_encodings.values())

    return known_student_ids, known_face_encodings


# ──────────────────────────────────────────────
# So khớp khuôn mặt
# ──────────────────────────────────────────────

def recognize_face(face_encoding, known_student_ids, known_face_encodings, tolerance=TOLERANCE):
    """
    So khớp 1 face encoding với danh sách encoding đã đăng ký.

    Trả về:
        student_id nếu nhận diện được
        None nếu không khớp
    """
    if not known_face_encodings:
        return None

    distances = face_recognition.face_distance(known_face_encodings, face_encoding)
    best_match_index = np.argmin(distances)
    best_distance = distances[best_match_index]

    if best_distance <= tolerance:
        return known_student_ids[best_match_index]

    return None


def recognize_faces_in_frame(frame, known_student_ids, known_face_encodings):
    """
    Nhận diện tất cả khuôn mặt trong 1 frame webcam.

    Trả về list dict:
        [
            {
                "student_id": "...",
                "name": "...",
                "location": (top, right, bottom, left)
            }
        ]
    """
    small_frame = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE_SCALE, fy=FRAME_RESIZE_SCALE)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(
        rgb_small_frame,
        number_of_times_to_upsample=1,
        model="hog"
    )

    face_encodings = face_recognition.face_encodings(
        rgb_small_frame,
        known_face_locations=face_locations
    )

    results = []

    for face_location, face_encoding in zip(face_locations, face_encodings):
        student_id = recognize_face(
            face_encoding,
            known_student_ids,
            known_face_encodings
        )

        name = "Unknown"

        if student_id:
            student = get_student(student_id)
            if student:
                name = student["full_name"]
            else:
                student_id = None

        top, right, bottom, left = face_location

        # Scale tọa độ từ small_frame về frame gốc
        top = int(top / FRAME_RESIZE_SCALE)
        right = int(right / FRAME_RESIZE_SCALE)
        bottom = int(bottom / FRAME_RESIZE_SCALE)
        left = int(left / FRAME_RESIZE_SCALE)

        results.append({
            "student_id": student_id,
            "name": name,
            "location": (top, right, bottom, left),
        })

    return results


# ──────────────────────────────────────────────
# Vẽ kết quả nhận diện lên frame
# ──────────────────────────────────────────────

def draw_recognition_results(frame, results):
    """
    Vẽ bounding box và tên sinh viên lên frame webcam.
    """
    for result in results:
        top, right, bottom, left = result["location"]
        name = result["name"]

        if result["student_id"]:
            box_color = (0, 255, 0)
        else:
            box_color = (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)

        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_color, cv2.FILLED)
        cv2.putText(
            frame,
            name,
            (left + 6, bottom - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    return frame


# ──────────────────────────────────────────────
# Flow điểm danh bằng webcam
# ──────────────────────────────────────────────

def run_face_attendance(subject=""):
    """
    Mở webcam, nhận diện khuôn mặt realtime và ghi điểm danh.

    Phím điều khiển:
        Q: thoát webcam

    Trả về:
        True nếu mở và chạy webcam thành công
        False nếu không có encoding hoặc không mở được webcam
    """
    create_tables()

    known_student_ids, known_face_encodings = get_known_face_data()

    if not known_student_ids:
        print("[Recognition] Chưa có dữ liệu khuôn mặt. Vui lòng đăng ký sinh viên trước.")
        return False

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[Recognition] Không mở được webcam. Kiểm tra camera.")
        return False

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    window_name = "Face Attendance - Recognition"
    cv2.namedWindow(window_name)

    frame_count = 0
    current_results = []
    marked_students = set()

    print("[Recognition] Đang chạy nhận diện. Nhấn Q để thoát.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("[Recognition] Không đọc được frame từ webcam.")
            break

        frame_count += 1

        if frame_count % DETECT_EVERY == 0:
            current_results = recognize_faces_in_frame(
                frame,
                known_student_ids,
                known_face_encodings
            )

            for result in current_results:
                student_id = result["student_id"]

                if student_id and student_id not in marked_students:
                    success, message = mark_attendance(student_id, subject)

                    if success:
                        marked_students.add(student_id)

                    print(message)

        display = draw_recognition_results(frame.copy(), current_results)

        cv2.putText(
            display,
            "Nhan Q de thoat",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (200, 200, 200),
            2
        )

        cv2.imshow(window_name, display)

        key = cv2.waitKey(1) & 0xFF

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break

        if key in (ord("q"), ord("Q")):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[Recognition] Đã dừng nhận diện.")
    return True


# ──────────────────────────────────────────────
# Flow test CLI
# ──────────────────────────────────────────────

def recognition_cli():
    """
    Menu test nhanh recognition.py bằng terminal.
    Chạy bằng lệnh:
        python -m modules.recognition
    """
    create_tables()

    while True:
        print("\n=== TEST RECOGNITION ===")
        print("1. Chạy nhận diện và điểm danh bằng webcam")
        print("0. Thoát")

        choice = input("Chọn chức năng: ").strip()

        if choice == "1":
            subject = input("Nhập môn học/lớp học phần (có thể bỏ trống): ").strip()
            run_face_attendance(subject)

        elif choice == "0":
            print("Đã thoát.")
            break

        else:
            print("Lựa chọn không hợp lệ.")


# ──────────────────────────────────────────────
# Test khi chạy trực tiếp
# ──────────────────────────────────────────────

if __name__ == "__main__":
    recognition_cli()