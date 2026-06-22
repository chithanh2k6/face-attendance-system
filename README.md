# Face Attendance System

Face Attendance System là ứng dụng desktop dùng để quản lý sinh viên, đăng ký khuôn mặt, nhận diện khuôn mặt bằng webcam và ghi nhận điểm danh tự động.

Dự án được xây dựng bằng Python, OpenCV, thư viện `face_recognition`, SQLite và CustomTkinter. Ứng dụng phù hợp cho đồ án sinh viên, dùng để demo quy trình điểm danh bằng nhận diện khuôn mặt trong môi trường lớp học.

Dự án được thực hiện bởi nhóm sinh viên với mục tiêu xây dựng một ứng dụng điểm danh tự động bằng nhận diện khuôn mặt phục vụ môi trường lớp học.

## 1. Chức năng chính

* Đăng ký sinh viên mới.
* Chụp ảnh khuôn mặt sinh viên bằng webcam.
* Trích xuất và lưu dữ liệu khuôn mặt.
* Nhận diện khuôn mặt theo thời gian thực.
* Ghi điểm danh tự động.
* Ghi nhận nhiều lượt điểm danh theo ngày và theo nội dung điểm danh.
* Quản lý danh sách sinh viên.
* Tìm kiếm sinh viên theo mã, họ tên hoặc lớp.
* Cập nhật thông tin sinh viên.
* Chụp lại ảnh khuôn mặt cho sinh viên.
* Xóa mềm sinh viên, giữ lại lịch sử điểm danh.
* Xem ảnh sinh viên.
* Xem lịch sử điểm danh của từng sinh viên.
* Dashboard tổng quan.
* Thống kê theo lớp hành chính.
* Thống kê theo nội dung điểm danh.
* Xuất báo cáo điểm danh ra CSV hoặc Excel.
* Hỗ trợ Light Mode và Dark Mode.

## 2. Công nghệ sử dụng

* Python 3.10.11
* OpenCV
* face_recognition
* dlib-bin
* SQLite
* CustomTkinter
* Pillow
* pandas
* openpyxl

## 3. Yêu cầu hệ thống

* Hệ điều hành: Windows 10 hoặc Windows 11.
* Python: khuyến nghị dùng Python 3.10.11.
* Máy tính có webcam.
* Webcam được cấp quyền truy cập.
* Nên chạy trong môi trường ảo `.venv`.

## 4. Cấu trúc thư mục

```text
face_attendance_app/
├── data/
│   ├── encodings/
│   │   └── .gitkeep
│   └── faces/
│       └── .gitkeep
├── modules/
│   ├── __init__.py
│   ├── attendance.py
│   ├── database.py
│   ├── recognition.py
│   ├── register.py
│   └── report.py
├── reports/
│   └── .gitkeep
├── ui/
│   ├── __init__.py
│   └── app.py
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## 5. Vai trò các thư mục và file chính

| Thành phần               | Vai trò                                                         |
| ------------------------ | --------------------------------------------------------------- |
| `main.py`                | File chạy chính của ứng dụng                                    |
| `ui/app.py`              | Giao diện desktop bằng CustomTkinter                            |
| `modules/database.py`    | Tạo database, bảng dữ liệu, CRUD sinh viên và truy vấn thống kê |
| `modules/register.py`    | Đăng ký sinh viên, chụp ảnh, tạo encoding khuôn mặt             |
| `modules/recognition.py` | Nhận diện khuôn mặt bằng webcam và gọi điểm danh                |
| `modules/attendance.py`  | Xử lý logic ghi điểm danh                                       |
| `modules/report.py`      | Xuất báo cáo CSV và Excel                                       |
| `data/faces/`            | Lưu ảnh khuôn mặt sinh viên                                     |
| `data/encodings/`        | Lưu file encoding khuôn mặt                                     |
| `reports/`               | Lưu các file báo cáo được xuất ra                               |
| `requirements.txt`       | Danh sách thư viện cần cài đặt                                  |

## 6. Cài đặt project

### Bước 1: Clone project

```powershell
git clone https://github.com/chithanh2k6/face-attendance-system.git
cd face-attendance-system
```

### Bước 2: Tạo môi trường ảo

```powershell
python -m venv .venv
```

### Bước 3: Kích hoạt môi trường ảo

```powershell
.\.venv\Scripts\activate
```

Sau khi kích hoạt thành công, terminal sẽ có dạng:

```text
(.venv) PS ...>
```

### Bước 4: Cài đặt thư viện

```powershell
pip install -r requirements.txt
```

Quá trình cài đặt có thể mất vài phút vì project sử dụng thư viện nhận diện khuôn mặt.

## 7. Chạy ứng dụng

Sau khi cài xong thư viện, chạy lệnh:

```powershell
python main.py
```

Ứng dụng sẽ tự động tạo các thư mục và file cần thiết nếu chưa tồn tại, bao gồm:

```text
data/
data/faces/
data/encodings/
reports/
data/attendance.db
```

## 8. Hướng dẫn sử dụng cơ bản

### 8.1. Đăng ký sinh viên

1. Mở tab `Đăng ký sinh viên`.
2. Nhập mã sinh viên, họ tên, lớp hành chính và giới tính.
3. Bấm `Đăng ký & Chụp ảnh`.
4. Webcam sẽ mở.
5. Nhấn `SPACE` để chụp ảnh khi khuôn mặt được nhận diện.
6. Nhấn `Q` để hủy nếu cần.

Mỗi sinh viên sẽ được chụp nhiều ảnh để tạo dữ liệu nhận diện khuôn mặt.

### 8.2. Điểm danh bằng webcam

1. Mở tab `Điểm danh`.
2. Nhập nội dung điểm danh nếu cần. Nội dung này có thể là tên môn học, lớp học phần, lớp hành chính, ca học hoặc buổi học cụ thể.
3. Bấm `Bắt đầu điểm danh`.
4. Webcam sẽ nhận diện khuôn mặt sinh viên.
5. Khi nhận diện đúng, hệ thống sẽ tự động ghi điểm danh.
6. Nhấn `Q` trong cửa sổ webcam để kết thúc.

Ví dụ nội dung điểm danh:

```text
Trí tuệ nhân tạo
Lập trình Python
Lập trình Python - Buổi sáng
Lập trình Python - Buổi chiều
CNTT01
Nhóm thực hành 1
```

Mỗi lượt nhận diện thành công sẽ được ghi nhận thành một bản ghi điểm danh. Nội dung điểm danh giúp phân loại dữ liệu theo môn học, lớp học phần, ca học hoặc buổi học khi xem lịch sử và xuất báo cáo.

### 8.3. Quản lý sinh viên

Trong tab `Quản lý sinh viên`, có thể:

* Xem danh sách sinh viên.
* Tìm kiếm sinh viên.
* Sửa thông tin sinh viên.
* Chụp lại ảnh khuôn mặt.
* Xem ảnh sinh viên.
* Xem lịch sử điểm danh.
* Xóa sinh viên khỏi danh sách hoạt động.

Khi xóa sinh viên, hệ thống chỉ xóa mềm. Lịch sử điểm danh vẫn được giữ lại để phục vụ báo cáo.

### 8.4. Xuất báo cáo

Trong tab `Xuất báo cáo`, có thể xuất dữ liệu theo:

* Toàn bộ dữ liệu.
* Theo ngày.
* Theo khoảng ngày.

Định dạng hỗ trợ:

* CSV
* Excel

File báo cáo sau khi xuất sẽ nằm trong thư mục:

```text
reports/
```

## 9. Dữ liệu phát sinh khi chạy app

Khi chạy ứng dụng, hệ thống có thể sinh ra các file dữ liệu như:

```text
data/attendance.db
data/faces/
data/encodings/encodings.pkl
reports/*.csv
reports/*.xlsx
```

Các file này không nên đưa lên GitHub nếu chứa dữ liệu thật hoặc ảnh khuôn mặt thật.

## 10. Lưu ý về quyền riêng tư

Project có sử dụng ảnh khuôn mặt sinh viên để demo nhận diện. Vì vậy:

* Không nên đẩy ảnh khuôn mặt thật lên GitHub công khai.
* Không nên đẩy file `attendance.db` nếu database có dữ liệu thật.
* Không nên đẩy file `encodings.pkl` nếu chứa dữ liệu khuôn mặt thật.
* Khi demo, nên dùng dữ liệu mẫu hoặc sinh viên demo đã đồng ý.

## 11. Lỗi thường gặp

### Lỗi không mở được webcam

Kiểm tra:

* Webcam có đang bị app khác sử dụng không.
* Windows đã cấp quyền camera chưa.
* Laptop có bật camera vật lý chưa.
* Có đang chạy app trong môi trường bị chặn camera không.

### Lỗi không nhận diện được khuôn mặt

Thử:

* Ngồi nơi đủ sáng.
* Nhìn thẳng vào camera.
* Không che mặt.
* Chụp lại ảnh đăng ký.
* Đăng ký nhiều ảnh rõ hơn.

### Lỗi cài thư viện face_recognition

Nên dùng Python 3.10.11 và cài lại trong môi trường ảo:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Lỗi thiếu thư mục `data` hoặc `reports`

Ứng dụng sẽ tự tạo các thư mục này khi chạy. Nếu cần tạo thủ công:

```powershell
mkdir data
mkdir data\faces
mkdir data\encodings
mkdir reports
```

## 12. Ghi chú khi demo

Trước khi demo, nên chuẩn bị sẵn:

* 3 đến 5 sinh viên mẫu.
* Mỗi sinh viên đã có ảnh khuôn mặt.
* Một vài lượt điểm danh mẫu.
* Một file báo cáo CSV hoặc Excel đã xuất thử.
* Webcam hoạt động ổn định.
* Môi trường `.venv` đã được cài đầy đủ thư viện.

## 13. Thành viên nhóm

| STT | Họ tên           | Vai trò / Công việc chính        |
| --- | ---------------- | -------------------------------- |
| 1   | Nguyễn Chí Thành | Leader, Core System, Integration |
| 2   | Hồ Minh Khuyến   | Database, Student Registration   |
| 3   | Phạm Minh Thiện  | UI Desktop                       |
| 4   | Lê Trung Hưng    | Reports, Documentation, Testing  |

## 14. Phạm vi đồ án

Project được xây dựng phục vụ mục đích học tập và demo đồ án sinh viên. Ứng dụng tập trung vào các chức năng chính gồm đăng ký sinh viên, lưu dữ liệu khuôn mặt, nhận diện khuôn mặt bằng webcam, ghi điểm danh tự động, quản lý sinh viên và xuất báo cáo.

Repository không bao gồm dữ liệu khuôn mặt thật, database thật hoặc file báo cáo đã xuất. Các dữ liệu này sẽ được tạo trong quá trình chạy ứng dụng hoặc chuẩn bị riêng cho buổi demo.

## 15. Hướng phát triển

* Thêm quản lý môn học, lớp học phần và buổi học riêng.
* Thêm danh sách sinh viên đăng ký theo từng lớp học phần.
* Thêm tài khoản đăng nhập cho giảng viên hoặc quản trị viên.
* Thêm biểu đồ thống kê trực quan.
* Xuất báo cáo PDF.
* Cải thiện độ chính xác nhận diện trong môi trường ánh sáng yếu.