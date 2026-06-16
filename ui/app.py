import tkinter as tk
from tkinter import ttk, messagebox
import threading
import customtkinter as ctk

from modules.database import (
    create_tables,
    get_all_students,
    delete_student,
)
from modules.register import (
    register_student_from_ui,
    remove_encoding,
)
from modules.recognition import run_face_attendance
from modules.attendance import get_today_attendance
from modules.report import (
    export_all_attendance,
    export_attendance_by_date,
)

# ──────────────────────────────────────────────
# Bảng màu & font
# ──────────────────────────────────────────────

COLORS_DARK = {
    "bg":           "#0F1117",
    "surface":      "#1A1D27",
    "surface_alt":  "#222535",
    "border":       "#2E3147",
    "accent":       "#4F8EF7",
    "accent_dim":   "#2D5BB5",
    "success":      "#3DD68C",
    "danger":       "#F75F5F",
    "warning":      "#F7C948",
    "text":         "#E8EAF0",
    "text_muted":   "#6B7280",
    "text_dim":     "#9CA3AF",
}

COLORS_LIGHT = {
    "bg":           "#F0F2F8",
    "surface":      "#FFFFFF",
    "surface_alt":  "#E8ECF5",
    "border":       "#D0D5E8",
    "accent":       "#3B7DE8",
    "accent_dim":   "#2660C4",
    "success":      "#1FAD6A",
    "danger":       "#E03C3C",
    "warning":      "#C8961A",
    "text":         "#1A1D2E",
    "text_muted":   "#717A96",
    "text_dim":     "#4E5770",
}

# Biến toàn cục lưu bảng màu hiện tại (mặc định Light)
COLORS = dict(COLORS_LIGHT)

FONT_HEADING  = ("Segoe UI", 18, "bold")
FONT_SUBHEAD  = ("Segoe UI", 11, "bold")
FONT_BODY     = ("Segoe UI", 10)
FONT_SMALL    = ("Segoe UI", 9)
FONT_MONO     = ("Consolas", 9)
FONT_BADGE    = ("Segoe UI", 8, "bold")

# ──────────────────────────────────────────────
# Theme helpers
# ──────────────────────────────────────────────

def _apply_theme(mode):
    """Cập nhật COLORS toàn cục theo mode 'light' hoặc 'dark'."""
    global COLORS
    if mode == "dark":
        COLORS.update(COLORS_DARK)
        ctk.set_appearance_mode("dark")
    else:
        COLORS.update(COLORS_LIGHT)
        ctk.set_appearance_mode("light")


def _darken(hex_color, amount=20):
    """Làm tối màu hex đơn giản cho hover effect."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r = max(0, r - amount)
    g = max(0, g - amount)
    b = max(0, b - amount)
    return f"#{r:02x}{g:02x}{b:02x}"


# ──────────────────────────────────────────────
# Widget helpers (CustomTkinter)
# ──────────────────────────────────────────────

def _flat_btn(parent, text, command, color=None, text_color=None,
              width=None, font=None, pady=8):
    """Tạo CTkButton bo góc, màu theo theme."""
    bg  = color or COLORS["accent"]
    fg  = text_color or COLORS["text"]
    btn = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=bg,
        text_color=fg,
        hover_color=_darken(bg, 24),
        font=font or ctk.CTkFont(family="Segoe UI", size=10),
        width=width or 0,
        corner_radius=8,
    )
    return btn


def _label(parent, text, font=None, color=None, **kw):
    """CTkLabel với style mặc định theo theme."""
    bg = kw.pop("bg", COLORS["bg"])
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(family=font[0], size=font[1],
                         weight="bold" if len(font) > 2 and "bold" in font[2] else "normal")
              if font else ctk.CTkFont(family="Segoe UI", size=10),
        text_color=color or COLORS["text"],
        fg_color=bg,
        **kw,
    )


def _separator(parent, bg=None):
    """Đường kẻ ngang phân cách."""
    return tk.Frame(parent, height=1, bg=bg or COLORS["border"])


def _entry(parent, textvariable=None, width=200, show=None):
    """CTkEntry field với style theme."""
    e = ctk.CTkEntry(
        parent,
        textvariable=textvariable,
        width=width,
        font=ctk.CTkFont(family="Segoe UI", size=10),
        fg_color=COLORS["surface_alt"],
        text_color=COLORS["text"],
        border_color=COLORS["border"],
        border_width=1,
        corner_radius=6,
        show=show or "",
    )
    return e


def _card(parent, **kw):
    """CTkFrame dạng card bo góc, có border nhẹ."""
    return ctk.CTkFrame(
        parent,
        fg_color=COLORS["surface"],
        corner_radius=12,
        border_width=1,
        border_color=COLORS["border"],
        **kw,
    )


# ──────────────────────────────────────────────
# Sidebar Nav Button
# ──────────────────────────────────────────────

class NavButton(ctk.CTkFrame):
    """
    Button điều hướng sidebar.
    Có icon text (emoji/ký tự) và label, highlight khi active.
    """
    def __init__(self, parent, icon, label, command, **kw):
        super().__init__(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=8,
            cursor="hand2",
            **kw,
        )
        self.command    = command
        self._active    = False
        self._bg_normal = COLORS["surface"]
        self._bg_hover  = COLORS["surface_alt"]
        self._bg_active = COLORS["accent"]

        self.icon_lbl = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(family="Segoe UI Emoji", size=14),
            text_color=COLORS["text_dim"],
            fg_color=self._bg_normal,
            width=32,
            anchor="center",
        )
        self.text_lbl = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_dim"],
            fg_color=self._bg_normal,
            anchor="w",
        )
        self.icon_lbl.pack(side="left", padx=(14, 6), pady=12)
        self.text_lbl.pack(side="left", padx=(0, 14), pady=12, fill="x", expand=True)

        for w in (self, self.icon_lbl, self.text_lbl):
            w.bind("<Button-1>", lambda e: self.command())
            w.bind("<Enter>",    self._on_hover)
            w.bind("<Leave>",    self._on_leave)

    def set_active(self, active):
        self._active = active
        bg   = self._bg_active if active else self._bg_normal
        fg   = COLORS["text"]  if active else COLORS["text_dim"]
        for w in (self, self.icon_lbl, self.text_lbl):
            w.configure(fg_color=bg)
        self.icon_lbl.configure(text_color=fg)
        font_weight = "bold" if active else "normal"
        self.text_lbl.configure(
            text_color=fg,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight=font_weight),
        )

    def refresh_colors(self):
        """Làm mới màu sau khi đổi theme."""
        self._bg_normal = COLORS["surface"]
        self._bg_hover  = COLORS["surface_alt"]
        self._bg_active = COLORS["accent"]
        self.set_active(self._active)

    def _on_hover(self, _):
        if not self._active:
            for w in (self, self.icon_lbl, self.text_lbl):
                w.configure(fg_color=self._bg_hover)

    def _on_leave(self, _):
        if not self._active:
            for w in (self, self.icon_lbl, self.text_lbl):
                w.configure(fg_color=self._bg_normal)

# ──────────────────────────────────────────────
# Treeview có scrollbar (danh sách sinh viên / điểm danh)
# ──────────────────────────────────────────────

class StyledTable(ctk.CTkFrame):
    """
    Wrapper cho ttk.Treeview với scrollbar dọc,
    áp dụng màu sắc phù hợp theme hiện tại.
    """
    def __init__(self, parent, columns, headings, col_widths=None, **kw):
        super().__init__(parent, fg_color=COLORS["surface"],
                         corner_radius=10, border_width=1,
                         border_color=COLORS["border"], **kw)

        self._columns   = columns
        self._headings  = headings
        self._col_widths = col_widths

        self._style = ttk.Style()
        self._apply_treeview_style()
        self._build_tree()

    def _apply_treeview_style(self):
        self._style.theme_use("clam")
        self._style.configure(
            "Dark.Treeview",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["surface"],
            rowheight=34,
            font=FONT_BODY,
            borderwidth=0,
        )
        self._style.configure(
            "Dark.Treeview.Heading",
            background=COLORS["surface_alt"],
            foreground=COLORS["text_dim"],
            font=FONT_SMALL,
            relief="flat",
            borderwidth=0,
        )
        self._style.map(
            "Dark.Treeview",
            background=[("selected", COLORS["accent_dim"])],
            foreground=[("selected", COLORS["text"])],
        )
        self._style.layout("Dark.Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"}),
        ])

    def _build_tree(self):
        """Tạo hoặc tạo lại Treeview và scrollbar bên trong frame."""
        for child in self.winfo_children():
            child.destroy()

        self.tree = ttk.Treeview(
            self,
            columns=self._columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
        )
        for i, col in enumerate(self._columns):
            w = self._col_widths[i] if self._col_widths else 120
            self.tree.heading(col, text=self._headings[i])
            self.tree.column(col, width=w, anchor="w", minwidth=40)

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        scroll.pack(side="right", fill="y", pady=2)

    def refresh_style(self):
        """Làm mới style Treeview sau khi đổi theme."""
        self._apply_treeview_style()
        self.configure(
            fg_color=COLORS["surface"],
            border_color=COLORS["border"],
        )

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def insert(self, values):
        self.tree.insert("", "end", values=values)

    def selected_values(self):
        sel = self.tree.selection()
        if sel:
            return self.tree.item(sel[0], "values")
        return None

# ──────────────────────────────────────────────
# Toast notification nhỏ góc dưới phải
# ──────────────────────────────────────────────

class Toast:
    """
    Thông báo nổi tạm thời (auto-dismiss sau 3 giây).
    Hiện ở góc dưới phải màn hình.
    """
    def __init__(self, root):
        self.root = root
        self._win = None

    def show(self, message, level="info"):
        color = {
            "info":    COLORS["accent"],
            "success": COLORS["success"],
            "error":   COLORS["danger"],
            "warning": COLORS["warning"],
        }.get(level, COLORS["accent"])

        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.95)
        win.configure(bg=color)

        # Padding frame
        frm = tk.Frame(win, bg=color, padx=18, pady=12)
        frm.pack()
        tk.Label(
            frm, text=message, font=FONT_BODY,
            fg="#FFFFFF", bg=color, wraplength=300, justify="left",
        ).pack()

        # Bo góc bằng highlight border cùng màu
        win.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww = win.winfo_reqwidth()
        wh = win.winfo_reqheight()
        win.geometry(f"+{sw - ww - 28}+{sh - wh - 64}")

        self._win = win
        self.root.after(3000, self._dismiss)

    def _dismiss(self):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

# ──────────────────────────────────────────────
# Panel: Đăng ký sinh viên
# ──────────────────────────────────────────────

class RegisterPanel(ctk.CTkFrame):
    """
    Form nhập thông tin và khởi động luồng đăng ký sinh viên.
    Nối với register_student_from_ui() từ modules/register.py.
    """
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        # Tiêu đề
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=32, pady=(28, 6))
        ctk.CTkLabel(
            header, text="Đăng ký sinh viên",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Nhập thông tin và chụp ảnh khuôn mặt qua webcam.",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _separator(self).pack(fill="x", padx=32, pady=(10, 0))

        # Form card
        card = _card(self)
        card.pack(fill="x", padx=32, pady=20)

        form = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        form.pack(padx=24, pady=20, anchor="w")

        # Các biến form
        self.var_id     = tk.StringVar()
        self.var_name   = tk.StringVar()
        self.var_class  = tk.StringVar()
        self.var_gender = tk.StringVar(value="Nam")

        fields = [
            ("MSSV *",      self.var_id,    False),
            ("Họ và tên *", self.var_name,  False),
            ("Lớp",         self.var_class, False),
        ]

        for label_text, var, _ in fields:
            row = ctk.CTkFrame(form, fg_color=COLORS["surface"])
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(
                row, text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
                width=110, anchor="w",
            ).pack(side="left")
            _entry(row, textvariable=var, width=260).pack(side="left", ipady=2)

        # Giới tính – radio buttons
        gender_row = ctk.CTkFrame(form, fg_color=COLORS["surface"])
        gender_row.pack(fill="x", pady=5)
        ctk.CTkLabel(
            gender_row, text="Giới tính",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=110, anchor="w",
        ).pack(side="left")
        for val in ("Nam", "Nữ"):
            tk.Radiobutton(
                gender_row, text=val, variable=self.var_gender, value=val,
                font=FONT_BODY, fg=COLORS["text"], bg=COLORS["surface"],
                selectcolor=COLORS["surface_alt"], activebackground=COLORS["surface"],
                activeforeground=COLORS["text"], bd=0, cursor="hand2",
            ).pack(side="left", padx=(0, 12))

        # Nút hành động
        btn_row = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        btn_row.pack(padx=24, pady=(0, 20), anchor="w")

        _flat_btn(
            btn_row, "Đăng ký & Chụp ảnh",
            command=self._start_register,
            color=COLORS["success"],
        ).pack(side="left", padx=(0, 10))
        _flat_btn(
            btn_row, "Xóa form",
            command=self._clear_form,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_muted"],
        ).pack(side="left")

        # Trạng thái
        self.status_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.status_lbl.pack(anchor="w", padx=32, pady=(0, 8))

        # Ghi chú
        note_frame = ctk.CTkFrame(
            self, fg_color=COLORS["surface_alt"],
            corner_radius=8, border_width=1, border_color=COLORS["border"],
        )
        note_frame.pack(fill="x", padx=32, pady=4)
        ctk.CTkLabel(
            note_frame,
            text="💡  Sau khi bấm đăng ký, webcam sẽ mở. Nhấn SPACE để chụp ảnh, Q để hủy.",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface_alt"],
            wraplength=560, justify="left",
        ).pack(padx=14, pady=10, anchor="w")

    # Hành động

    def _clear_form(self):
        self.var_id.set("")
        self.var_name.set("")
        self.var_class.set("")
        self.var_gender.set("Nam")

    def _start_register(self):
        student_id = self.var_id.get().strip()
        full_name  = self.var_name.get().strip()
        class_name = self.var_class.get().strip()
        gender     = self.var_gender.get().strip()

        if not student_id or not full_name:
            self.toast.show("Vui lòng nhập MSSV và Họ tên.", "warning")
            return

        self._set_status("⏳  Đang khởi động webcam...", COLORS["warning"])

        # Chạy trong thread riêng để không treo UI
        def _run():
            status, msg = register_student_from_ui(
                student_id, full_name, class_name, gender
            )
            self.after(
                0,
                lambda: self._handle_register_result(
                    status, msg, student_id, full_name, class_name, gender
                ),
            )

        threading.Thread(target=_run, daemon=True).start()

    def _handle_register_result(self, status, msg, sid, fname, cname, gender):
        """Xử lý kết quả trả về từ register_student_from_ui."""
        if status == "SUCCESS":
            self._set_status(f"✅  {msg}", COLORS["success"])
            self.toast.show(msg, "success")
            self._clear_form()

        elif status == "PROMPT_RECOVER":
            # Hỏi người dùng có muốn khôi phục không
            answer = messagebox.askyesno(
                "Phát hiện sinh viên cũ",
                msg + "\n\nBạn có muốn khôi phục không?",
            )
            if answer:
                self._set_status("⏳  Đang khởi động webcam để chụp lại ảnh...", COLORS["warning"])

                def _recover():
                    s2, m2 = register_student_from_ui(
                        sid, fname, cname, gender, force_recover=True
                    )

                    def _update_ui():
                        if s2 == "SUCCESS":
                            self._set_status(f"✅  {m2}", COLORS["success"])
                            self.toast.show(m2, "success")
                            self._clear_form()
                        else:
                            self._set_status(f"❌  {m2}", COLORS["danger"])
                            self.toast.show(m2, "error")

                    self.after(0, _update_ui)

                threading.Thread(target=_recover, daemon=True).start()
            else:
                self._set_status("Đã hủy khôi phục.", COLORS["text_muted"])

        elif status == "EXISTS":
            self._set_status(f"⚠️  {msg}", COLORS["warning"])
            self.toast.show(msg, "warning")

        else:
            self._set_status(f"❌  {msg}", COLORS["danger"])
            self.toast.show(msg, "error")

    def _set_status(self, text, color):
        """Cập nhật label trạng thái (an toàn từ thread phụ)."""
        self.after(0, lambda: self.status_lbl.configure(text=text, text_color=color))


# ──────────────────────────────────────────────
# Panel: Nhận diện & Điểm danh
# ──────────────────────────────────────────────

class RecognitionPanel(ctk.CTkFrame):
    """
    Mở webcam nhận diện khuôn mặt realtime và ghi điểm danh tự động.
    Nối với run_face_attendance() từ modules/recognition.py.
    """
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast    = toast
        self._running = False
        self._build()

    def _build(self):
        # Tiêu đề
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=32, pady=(28, 6))
        ctk.CTkLabel(
            header, text="Nhận diện & Điểm danh",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Bật webcam để nhận diện khuôn mặt và điểm danh tự động.",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _separator(self).pack(fill="x", padx=32, pady=(10, 0))

        # Tùy chọn môn học
        opt_card = _card(self)
        opt_card.pack(fill="x", padx=32, pady=20)
        inner = ctk.CTkFrame(opt_card, fg_color=COLORS["surface"])
        inner.pack(padx=24, pady=16, anchor="w")

        ctk.CTkLabel(
            inner, text="Môn học / Lớp học phần",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(0, 8))
        self.var_subject = tk.StringVar()
        _entry(inner, textvariable=self.var_subject, width=300).pack(
            anchor="w", ipady=2)
        ctk.CTkLabel(
            inner,
            text="Để trống nếu không cần phân biệt theo môn.",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(4, 0))

        # Nút
        btn_card = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        btn_card.pack(fill="x", padx=32)
        self.btn_start = _flat_btn(
            btn_card, "▶  Bắt đầu điểm danh",
            command=self._start_recognition,
            color=COLORS["success"],
        )
        self.btn_start.pack(side="left", padx=(0, 12))

        # Trạng thái
        self.status_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.status_lbl.pack(anchor="w", padx=32, pady=(14, 0))

        # Ghi chú
        note_frame = ctk.CTkFrame(
            self, fg_color=COLORS["surface_alt"],
            corner_radius=8, border_width=1, border_color=COLORS["border"],
        )
        note_frame.pack(fill="x", padx=32, pady=16)
        ctk.CTkLabel(
            note_frame,
            text=(
                "💡  Webcam sẽ nhận diện khuôn mặt liên tục.\n"
                "     Mỗi sinh viên chỉ được ghi điểm danh một lần mỗi ngày.\n"
                "     Nhấn Q trong cửa sổ webcam để kết thúc."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface_alt"],
            justify="left",
        ).pack(padx=14, pady=10, anchor="w")

    def _start_recognition(self):
        if self._running:
            self.toast.show("Webcam đang chạy, hãy đóng cửa sổ camera trước.", "warning")
            return

        subject = self.var_subject.get().strip()
        self._set_status("⏳  Đang mở webcam...", COLORS["warning"])
        self.btn_start.configure(state="disabled")
        self._running = True

        def _run():
            result = run_face_attendance(subject)

            def _update_ui():
                self._running = False
                self.btn_start.configure(state="normal")
                if result:
                    self._set_status("✅  Đã kết thúc phiên điểm danh.", COLORS["success"])
                    self.toast.show("Phiên điểm danh kết thúc.", "success")
                else:
                    self._set_status(
                        "❌  Không thể mở webcam hoặc chưa có dữ liệu khuôn mặt.",
                        COLORS["danger"],
                    )
                    self.toast.show("Không thể bắt đầu nhận diện.", "error")

            self.after(0, _update_ui)

        threading.Thread(target=_run, daemon=True).start()

    def _set_status(self, text, color):
        self.after(0, lambda: self.status_lbl.configure(text=text, text_color=color))

# ──────────────────────────────────────────────
# Panel: Xem điểm danh hôm nay
# ──────────────────────────────────────────────

class AttendancePanel(ctk.CTkFrame):
    """
    Hiển thị danh sách điểm danh trong ngày hiện tại.
    Tải dữ liệu từ get_today_attendance() trong modules/attendance.py.
    """
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        # Tiêu đề + nút làm mới
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=32, pady=(28, 6))
        ctk.CTkLabel(
            header, text="Điểm danh hôm nay",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(side="left", anchor="w")
        _flat_btn(
            header, "🔄  Tải lại",
            command=self.load_data,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(family="Segoe UI", size=9),
        ).pack(side="right", pady=4)
        _separator(self).pack(fill="x", padx=32, pady=(10, 0))

        # Đếm badge
        info_row = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        info_row.pack(fill="x", padx=32, pady=(12, 6))
        self.count_lbl = ctk.CTkLabel(
            info_row, text="0 sinh viên đã điểm danh",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.count_lbl.pack(side="left")

        # Bảng dữ liệu
        cols   = ("student_id", "full_name", "class_name", "time", "subject")
        heads  = ("MSSV", "Họ và tên", "Lớp", "Giờ điểm danh", "Môn học")
        widths = [120, 200, 120, 120, 160]
        self.table = StyledTable(self, columns=cols, headings=heads, col_widths=widths)
        self.table.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        self.load_data()

    def load_data(self):
        """Tải lại dữ liệu điểm danh hôm nay."""
        records = get_today_attendance()
        self.table.clear()
        for r in records:
            self.table.insert((
                r.get("student_id", ""),
                r.get("full_name", ""),
                r.get("class_name", "") or "—",
                r.get("time", ""),
                r.get("subject", "") or "—",
            ))
        count = len(records)
        self.count_lbl.configure(
            text=f"{'Chưa có' if count == 0 else count} sinh viên đã điểm danh hôm nay.",
        )

# ──────────────────────────────────────────────
# Panel: Quản lý sinh viên + xóa
# ──────────────────────────────────────────────

class StudentsPanel(ctk.CTkFrame):
    """
    Danh sách toàn bộ sinh viên đang hoạt động.
    Cho phép xóa mềm (soft delete) kèm xóa encoding.
    """
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=32, pady=(28, 6))
        ctk.CTkLabel(
            header, text="Quản lý sinh viên",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(side="left", anchor="w")
        _flat_btn(
            header, "🔄  Tải lại",
            command=self.load_data,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(family="Segoe UI", size=9),
        ).pack(side="right", pady=4)
        _separator(self).pack(fill="x", padx=32, pady=(10, 0))

        # Đếm
        self.count_lbl = ctk.CTkLabel(
            self, text="...",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.count_lbl.pack(anchor="w", padx=32, pady=(8, 4))

        # Bảng
        cols   = ("student_id", "full_name", "class_name", "gender", "created_at")
        heads  = ("MSSV", "Họ và tên", "Lớp", "Giới tính", "Ngày đăng ký")
        widths = [120, 200, 120, 90, 160]
        self.table = StyledTable(self, columns=cols, headings=heads, col_widths=widths)
        self.table.pack(fill="both", expand=True, padx=32, pady=(0, 12))

        # Nút xóa
        btn_row = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        btn_row.pack(fill="x", padx=32, pady=(0, 20))
        _flat_btn(
            btn_row, "🗑  Xóa sinh viên đã chọn",
            command=self._delete_selected,
            color=COLORS["danger"],
        ).pack(side="left")
        ctk.CTkLabel(
            btn_row,
            text="Chọn một hàng rồi bấm xóa. Lịch sử điểm danh vẫn được giữ lại.",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(side="left", padx=(14, 0))

        self.load_data()

    def load_data(self):
        students = get_all_students()
        self.table.clear()
        for s in students:
            self.table.insert((
                s.get("student_id", ""),
                s.get("full_name", ""),
                s.get("class_name", "") or "—",
                s.get("gender", "") or "—",
                (s.get("created_at", "") or "")[:10],
            ))
        self.count_lbl.configure(text=f"{len(students)} sinh viên đang hoạt động.")

    def _delete_selected(self):
        vals = self.table.selected_values()
        if not vals:
            self.toast.show("Hãy chọn một sinh viên trong danh sách.", "warning")
            return

        sid  = vals[0]
        name = vals[1]
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa sinh viên:\n\n  {name} ({sid})?\n\n"
            "Lịch sử điểm danh sẽ được giữ lại, nhưng sinh viên này\n"
            "sẽ không thể điểm danh nữa.",
        )
        if not confirm:
            return

        # Xóa mềm trong DB + xóa encoding để không bị nhận diện nữa
        deleted = delete_student(sid)
        if deleted:
            remove_encoding(sid)
            self.toast.show(f"Đã xóa: {name} ({sid})", "success")
            self.load_data()
        else:
            self.toast.show("Không thể xóa. Sinh viên có thể đã bị xóa rồi.", "error")

# ──────────────────────────────────────────────
# Panel: Xuất báo cáo CSV
# ──────────────────────────────────────────────

class ReportPanel(ctk.CTkFrame):
    """
    Xuất báo cáo điểm danh ra file CSV.
    Nối với export_all_attendance() và export_attendance_by_date() từ modules/report.py.
    """
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=32, pady=(28, 6))
        ctk.CTkLabel(
            header, text="Xuất báo cáo",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Xuất dữ liệu điểm danh ra file CSV trong thư mục reports/.",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _separator(self).pack(fill="x", padx=32, pady=(10, 0))

        # Card
        card = _card(self)
        card.pack(fill="x", padx=32, pady=20)
        inner = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        inner.pack(padx=24, pady=20, anchor="w")

        ctk.CTkLabel(
            inner, text="Xuất toàn bộ lịch sử điểm danh",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text="File CSV sẽ bao gồm: MSSV · Họ tên · Lớp · Ngày · Giờ · Trạng thái · Môn học",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(4, 12))

        btn_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        btn_row.pack(anchor="w")
        _flat_btn(
            btn_row, "Xuất toàn bộ ra CSV",
            command=self._export_all,
            color=COLORS["success"],
        ).pack(side="left")

        _separator(inner, bg=COLORS["border"]).pack(fill="x", pady=16)

        ctk.CTkLabel(
            inner, text="Xuất điểm danh theo ngày",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text="Nhập ngày theo định dạng YYYY-MM-DD, ví dụ: 2026-06-01",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(4, 8))

        date_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        date_row.pack(anchor="w")
        self.var_report_date = tk.StringVar()
        _entry(date_row, textvariable=self.var_report_date, width=180).pack(side="left", ipady=2)
        _flat_btn(
            date_row, "Xuất theo ngày",
            command=self._export_by_date,
            color=COLORS["success"],
        ).pack(side="left", padx=(10, 0))

        # Log
        _separator(self).pack(fill="x", padx=32, pady=(0, 12))
        ctk.CTkLabel(
            self, text="Nhật ký xuất báo cáo:",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", padx=32)

        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=9),
            fg_color=COLORS["surface"],
            text_color=COLORS["text_dim"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=10,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=32, pady=(4, 24))

    def _log(self, msg, color=None):
        """Thêm dòng vào text log."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _export_all(self):
        self._log("⏳ Đang xuất toàn bộ dữ liệu...")

        def _run():
            success, message = export_all_attendance()
            self.after(0, lambda: self._on_export_done(success, message))

        threading.Thread(target=_run, daemon=True).start()

    def _export_by_date(self):
        date = self.var_report_date.get().strip()

        if not date:
            self.toast.show("Vui lòng nhập ngày cần xuất báo cáo.", "warning")
            return

        self._log(f"⏳ Đang xuất dữ liệu ngày {date}...")

        def _run():
            success, message = export_attendance_by_date(date)
            self.after(0, lambda: self._on_export_done(success, message))

        threading.Thread(target=_run, daemon=True).start()

    def _on_export_done(self, success, message):
        if success:
            self._log(f"✅ {message}")
            self.toast.show("Xuất báo cáo thành công!", "success")
        else:
            self._log(f"❌ {message}")
            self.toast.show(message, "error")

# ──────────────────────────────────────────────
# Cửa sổ chính: FaceAttendanceApp
# ──────────────────────────────────────────────

class FaceAttendanceApp(ctk.CTk):
    """
    Cửa sổ chính của ứng dụng Face Attendance.
    Gồm sidebar điều hướng (trái) và vùng nội dung thay đổi (phải).
    Hỗ trợ chuyển đổi Light/Dark mode qua sidebar.
    """

    def __init__(self):
        # Mặc định Light Mode
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        _apply_theme("light")

        super().__init__()
        create_tables()
        self._current_mode = "light"
        self._setup_window()
        self.toast = Toast(self)
        self._panels = {}
        self._nav_btns = {}
        self._build_layout()
        self._show_panel("attendance")   # mặc định mở trang điểm danh hôm nay

    # Cài đặt cửa sổ

    def _setup_window(self):
        self.title("Face Attendance System")
        self.geometry("1060x680")
        self.minsize(820, 540)
        self.configure(fg_color=COLORS["bg"])
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    # Layout chính

    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=0,
            width=210,
            border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Vùng content
        self.content_area = ctk.CTkFrame(
            self, fg_color=COLORS["bg"], corner_radius=0,
        )
        self.content_area.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_panels()

    def _build_sidebar(self):
        # Logo / tên app
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface"])
        logo_frame.pack(fill="x", pady=(22, 8))
        ctk.CTkLabel(
            logo_frame, text="👁  FaceAttend",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(padx=18, anchor="w")
        ctk.CTkLabel(
            logo_frame, text="v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(padx=18, anchor="w")

        _separator(self.sidebar, bg=COLORS["border"]).pack(fill="x", padx=12, pady=8)

        # Mục điều hướng
        nav_items = [
            ("attendance",  "📋", "Hôm nay"),
            ("recognition", "🎥", "Điểm danh"),
            ("register",    "➕", "Đăng ký sinh viên"),
            ("students",    "👥", "Quản lý sinh viên"),
            ("report",      "📊", "Xuất báo cáo"),
        ]

        for key, icon, label in nav_items:
            btn = NavButton(
                self.sidebar, icon, label,
                command=lambda k=key: self._show_panel(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_btns[key] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface"]).pack(
            fill="both", expand=True,
        )

        # Nút chuyển Light / Dark
        _separator(self.sidebar, bg=COLORS["border"]).pack(fill="x", padx=12, pady=(8, 6))

        theme_row = ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface"])
        theme_row.pack(anchor="center", pady=(0, 6))

        ctk.CTkLabel(
            theme_row, text="🌙  Dark",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(side="left", padx=(0, 6))

        self.theme_switch = ctk.CTkSwitch(
            theme_row,
            text="",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light",
            width=44,
            height=22,
            progress_color=COLORS["accent"],
            button_color=COLORS["surface"],
            button_hover_color=COLORS["surface_alt"],
            fg_color=COLORS["border"],
        )
        # Mặc định Light → switch OFF
        self.theme_switch.pack(side="left", pady=6)

        # Giữ đúng trạng thái switch sau khi rebuild theme
        if self._current_mode == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        # Footer sidebar
        _separator(self.sidebar, bg=COLORS["border"]).pack(fill="x", padx=12, pady=(6, 6))
        ctk.CTkLabel(
            self.sidebar, text="Python · OpenCV · SQLite",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="center", pady=(0, 16))

    def _build_panels(self):
        """Khởi tạo tất cả panel một lần, dùng pack/pack_forget để toggle."""
        panels = {
            "attendance":  AttendancePanel(self.content_area,  self.toast),
            "recognition": RecognitionPanel(self.content_area, self.toast),
            "register":    RegisterPanel(self.content_area,    self.toast),
            "students":    StudentsPanel(self.content_area,    self.toast),
            "report":      ReportPanel(self.content_area,      self.toast),
        }
        for key, panel in panels.items():
            self._panels[key] = panel

    def _show_panel(self, key):
        """Ẩn tất cả panel, hiện panel theo key, cập nhật sidebar active."""
        for k, panel in self._panels.items():
            panel.pack_forget()
        for k, btn in self._nav_btns.items():
            btn.set_active(k == key)

        panel = self._panels[key]
        panel.pack(fill="both", expand=True)

        # Tải lại dữ liệu nếu panel có hàm load_data
        if hasattr(panel, "load_data"):
            panel.load_data()

    # Chuyển đổi theme

    def _toggle_theme(self):
        """Chuyển đổi giữa Light và Dark mode, cập nhật toàn bộ UI."""
        new_mode = self.theme_switch.get()
        _apply_theme(new_mode)
        self._current_mode = new_mode

        # Lưu panel hiện tại trước khi rebuild UI
        self._active_panel_key = next(
            (k for k, btn in self._nav_btns.items() if btn._active),
            "attendance",
        )

        self.configure(fg_color=COLORS["bg"])
        self.content_area.configure(fg_color=COLORS["bg"])
        self.sidebar.configure(fg_color=COLORS["surface"])

        self._rebuild_all()

    def _rebuild_all(self):
        """
        Rebuild sidebar và tất cả panel sau khi đổi theme.
        Giữ nguyên trạng thái active panel hiện tại.
        """
        # Lấy panel đã lưu trước khi rebuild
        active_key = getattr(self, "_active_panel_key", "attendance")

        # Xóa và build lại sidebar (ngoại trừ area content)
        for child in self.sidebar.winfo_children():
            child.destroy()
        self._nav_btns.clear()
        self._build_sidebar()

        # Xóa và build lại tất cả panels
        for child in self.content_area.winfo_children():
            child.destroy()
        self._panels.clear()
        self._build_panels()

        # Khôi phục panel active
        self._show_panel(active_key)

# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def run_app():
    """
    Khởi động ứng dụng Face Attendance.
    Gọi từ main.py hoặc chạy trực tiếp file này.
    """
    app = FaceAttendanceApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
