import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from datetime import datetime
import customtkinter as ctk
from PIL import Image, ImageTk

from modules.database import (
    create_tables,
    get_all_students,
    search_students,
    get_student,
    update_student,
    delete_student,
    get_attendance_by_student,
    get_total_students,
    get_today_attendance_count,
    get_not_attended_today_count,
    get_total_attendance_count,
    get_class_statistics,
    get_subject_statistics,
    get_all_attendance,
    get_recent_attendance,
    FACES_DIR,
)
from modules.register import (
    register_student_from_ui,
    remove_encoding,
    update_face_from_ui,
)
from modules.recognition import run_face_attendance
from modules.report import export_attendance_report

# ──────────────────────────────────────────────
# Bảng màu & font — phong cách "Academic Precision"
# ──────────────────────────────────────────────

COLORS_LIGHT = {
    "bg":           "#F8FAFC",   # nền chính (slate-50)
    "surface":      "#FFFFFF",   # card / panel
    "surface_alt":  "#F1F5F9",   # hover / row alt (slate-100)
    "border":       "#E2E8F0",   # viền nhẹ (slate-200)
    "accent":       "#2563EB",   # xanh dương chủ đạo (blue-600)
    "accent_dim":   "#1D4ED8",   # accent tối hơn, dùng khi hover (blue-700)
    "success":      "#10B981",   # xanh lá (emerald-500)
    "danger":       "#EF4444",   # đỏ (red-500)
    "warning":      "#F59E0B",   # vàng cam (amber-500)
    "text":         "#0F172A",   # chữ chính (slate-900)
    "text_muted":   "#64748B",   # chữ phụ (slate-500)
    "text_dim":     "#334155",   # chữ nhạt hơn chữ chính (slate-700)
    "on_accent":    "#FFFFFF",   # chữ đặt trên nền accent
}

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
    "on_accent":    "#0F1117",
}

# Biến toàn cục lưu bảng màu hiện tại (mặc định Light)
COLORS = dict(COLORS_LIGHT)

# Hằng số bố cục dùng chung — giữ đồng bộ khoảng cách toàn app
SIDEBAR_WIDTH  = 240
CONTENT_PADX   = 24
CARD_RADIUS    = 12
BTN_RADIUS     = 8
ENTRY_RADIUS   = 8


FONT_HEADING  = ("Segoe UI", 24, "bold")
FONT_SUBHEAD  = ("Segoe UI", 16, "bold")
FONT_BODY     = ("Segoe UI", 14)
FONT_SMALL    = ("Segoe UI", 13)
FONT_MONO     = ("Consolas", 12)
FONT_BADGE    = ("Segoe UI", 11, "bold")

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
    bg = color or COLORS["accent"]
    fg = text_color or COLORS["on_accent"]
    btn = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=bg,
        text_color=fg,
        hover_color=_darken(bg, 24),
        font=font or ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        width=width or 0,
        height=38, # Nâng chiều cao nút
        corner_radius=BTN_RADIUS,
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
              if font else ctk.CTkFont(family="Segoe UI", size=13),
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
        height=38, # Nâng chiều cao ô nhập
        font=ctk.CTkFont(family="Segoe UI", size=13),
        fg_color=COLORS["surface"],
        text_color=COLORS["text"],
        border_color=COLORS["border"],
        border_width=1,
        corner_radius=ENTRY_RADIUS,
        show=show or "",
    )
    return e


def _card(parent, **kw):
    """CTkFrame dạng card bo góc, có border nhẹ."""
    return ctk.CTkFrame(
        parent,
        fg_color=COLORS["surface"],
        corner_radius=CARD_RADIUS,
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
            corner_radius=BTN_RADIUS,
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
            font=ctk.CTkFont(family="Segoe UI Emoji", size=18),
            text_color=COLORS["text_dim"],
            fg_color=self._bg_normal,
            width=28,
            anchor="center",
        )
        self.text_lbl = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text_dim"],
            fg_color=self._bg_normal,
            anchor="w",
        )
        self.icon_lbl.pack(side="left", padx=(14, 6), pady=11)
        self.text_lbl.pack(side="left", padx=(0, 14), pady=11, fill="x", expand=True)

        for w in (self, self.icon_lbl, self.text_lbl):
            w.bind("<Button-1>", lambda e: self.command())
            w.bind("<Enter>",    self._on_hover)
            w.bind("<Leave>",    self._on_leave)

    def set_active(self, active):
        self._active = active
        bg = self._bg_active if active else self._bg_normal
        fg = COLORS["on_accent"] if active else COLORS["text_dim"]
        for w in (self, self.icon_lbl, self.text_lbl):
            w.configure(fg_color=bg)
        self.icon_lbl.configure(text_color=fg)
        font_weight = "bold" if active else "normal"
        self.text_lbl.configure(
            text_color=fg,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight=font_weight),
        )

    def refresh_colors(self):
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
    def __init__(self, parent, columns, headings, col_widths=None,
                 col_alignments=None, rows=None, **kw):
        super().__init__(parent, fg_color=COLORS["surface"],
                         corner_radius=10, border_width=1,
                         border_color=COLORS["border"], **kw)

        self._columns        = columns
        self._headings       = headings
        self._col_widths     = col_widths
        self._col_alignments = col_alignments
        self._rows           = rows

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
            rowheight=36, # Mở rộng khoảng cách dòng cho chữ to
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
            padding=(0, 6)
        )
        self._style.map(
            "Dark.Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["on_accent"])],
        )
        self._style.layout("Dark.Treeview", [
            ("Treeview.treearea", {"sticky": "nswe"}),
        ])

    def _build_tree(self):
        for child in self.winfo_children():
            child.destroy()

        tree_options = {
            "columns": self._columns,
            "show": "headings",
            "style": "Dark.Treeview",
            "selectmode": "browse",
        }
        if self._rows is not None:
            tree_options["height"] = self._rows

        self.tree = ttk.Treeview(self, **tree_options)
        for i, col in enumerate(self._columns):
            w = self._col_widths[i] if self._col_widths else 120
            align = self._col_alignments[i] if self._col_alignments else "w"
            self.tree.heading(col, text=self._headings[i], anchor="center")
            self.tree.column(col, width=w, anchor=align, minwidth=40)

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        scroll.pack(side="right", fill="y", pady=2)

    def refresh_style(self):
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
        symbol = {
            "info":    "i",
            "success": "✓",
            "error":   "×",
            "warning": "!",
        }.get(level, "i")
        display_message = f"{symbol}  {message}"

        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.97)
        win.configure(bg=color)

        frm = tk.Frame(win, bg=color, padx=18, pady=12)
        frm.pack()
        tk.Label(
            frm, text=display_message, font=FONT_BODY,
            fg="#FFFFFF", bg=color, wraplength=300, justify="left",
        ).pack()

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
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=CONTENT_PADX, pady=(26, 6))
        ctk.CTkLabel(
            header, text="Đăng ký sinh viên",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Nhập thông tin và chụp ảnh khuôn mặt qua webcam.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _separator(self).pack(fill="x", padx=CONTENT_PADX, pady=(10, 0))

        card = _card(self)
        card.pack(fill="x", padx=CONTENT_PADX, pady=18)

        form = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        form.pack(padx=22, pady=18, anchor="w")

        self.var_id     = tk.StringVar()
        self.var_name   = tk.StringVar()
        self.var_class  = tk.StringVar()
        self.var_gender = tk.StringVar(value="Nam")

        fields = [
            ("Mã sinh viên *", self.var_id,    False),
            ("Họ và tên *", self.var_name,  False),
            ("Lớp hành chính", self.var_class, False),
        ]

        for label_text, var, _ in fields:
            row = ctk.CTkFrame(form, fg_color=COLORS["surface"])
            row.pack(fill="x", pady=8)
            ctk.CTkLabel(
                row, text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
                width=130, anchor="w",
            ).pack(side="left")
            _entry(row, textvariable=var, width=280).pack(side="left")

        gender_row = ctk.CTkFrame(form, fg_color=COLORS["surface"])
        gender_row.pack(fill="x", pady=8)
        ctk.CTkLabel(
            gender_row, text="Giới tính",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=130, anchor="w",
        ).pack(side="left")
        for val in ("Nam", "Nữ"):
            tk.Radiobutton(
                gender_row, text=val, variable=self.var_gender, value=val,
                font=FONT_BODY, fg=COLORS["text"], bg=COLORS["surface"],
                selectcolor=COLORS["surface_alt"], activebackground=COLORS["surface"],
                activeforeground=COLORS["text"], bd=0, cursor="hand2",
            ).pack(side="left", padx=(0, 16))

        btn_row = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        btn_row.pack(padx=22, pady=(0, 18), anchor="w")

        _flat_btn(
            btn_row, "Đăng ký & Chụp ảnh",
            command=self._start_register,
            color=COLORS["success"],
        ).pack(side="left", padx=(0, 12))
        _flat_btn(
            btn_row, "Xóa form",
            command=self._clear_form,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.status_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.status_lbl.pack(anchor="w", padx=CONTENT_PADX, pady=(0, 8))

        note_frame = ctk.CTkFrame(
            self, fg_color=COLORS["surface_alt"],
            corner_radius=BTN_RADIUS, border_width=1, border_color=COLORS["border"],
        )
        note_frame.pack(fill="x", padx=CONTENT_PADX, pady=4)
        ctk.CTkLabel(
            note_frame,
            text="Lưu ý: Sau khi bấm đăng ký, webcam sẽ mở. Nhấn SPACE để chụp ảnh, Q để hủy.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface_alt"],
            wraplength=600, justify="left",
        ).pack(padx=16, pady=12, anchor="w")

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
            self.toast.show("Vui lòng nhập Mã sinh viên và Họ tên.", "warning")
            return

        self._set_status("Đang khởi động webcam...", COLORS["warning"])

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
        if status == "SUCCESS":
            self._set_status(msg, COLORS["success"])
            self.toast.show(msg, "success")
            self._clear_form()
        elif status == "PROMPT_RECOVER":
            answer = messagebox.askyesno(
                "Phát hiện sinh viên cũ",
                msg + "\n\nBạn có muốn khôi phục không?",
            )
            if answer:
                self._set_status("Đang khởi động webcam để chụp lại ảnh...", COLORS["warning"])
                def _recover():
                    s2, m2 = register_student_from_ui(
                        sid, fname, cname, gender, force_recover=True
                    )
                    def _update_ui():
                        if s2 == "SUCCESS":
                            self._set_status(m2, COLORS["success"])
                            self.toast.show(m2, "success")
                            self._clear_form()
                        else:
                            self._set_status(m2, COLORS["danger"])
                            self.toast.show(m2, "error")
                    self.after(0, _update_ui)
                threading.Thread(target=_recover, daemon=True).start()
            else:
                self._set_status("Đã hủy khôi phục.", COLORS["text_muted"])
        elif status == "EXISTS":
            self._set_status(msg, COLORS["warning"])
            self.toast.show(msg, "warning")
        else:
            self._set_status(msg, COLORS["danger"])
            self.toast.show(msg, "error")

    def _set_status(self, text, color):
        self.after(0, lambda: self.status_lbl.configure(text=text, text_color=color))

# ──────────────────────────────────────────────
# Panel: Nhận diện & Điểm danh
# ──────────────────────────────────────────────

class RecognitionPanel(ctk.CTkFrame):
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast    = toast
        self._running = False
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=CONTENT_PADX, pady=(26, 6))
        ctk.CTkLabel(
            header, text="Nhận diện & Điểm danh",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Bật webcam để nhận diện khuôn mặt và điểm danh tự động.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _separator(self).pack(fill="x", padx=CONTENT_PADX, pady=(10, 0))

        opt_card = _card(self)
        opt_card.pack(fill="x", padx=CONTENT_PADX, pady=18)
        inner = ctk.CTkFrame(opt_card, fg_color=COLORS["surface"])
        inner.pack(padx=22, pady=16, anchor="w")

        ctk.CTkLabel(
            inner, text="Nội dung điểm danh",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(0, 8))
        self.var_subject = tk.StringVar()
        _entry(inner, textvariable=self.var_subject, width=350).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text="Nhập môn / lớp học phần hoặc lớp hành chính nếu cần điểm danh nhiều buổi trong cùng ngày.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(6, 0))

        btn_card = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        btn_card.pack(fill="x", padx=CONTENT_PADX)
        self.btn_start = _flat_btn(
            btn_card, "▶  Bắt đầu điểm danh",
            command=self._start_recognition,
            color=COLORS["success"],
        )
        self.btn_start.pack(side="left", padx=(0, 12))

        self.status_lbl = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.status_lbl.pack(anchor="w", padx=CONTENT_PADX, pady=(14, 0))

        note_frame = ctk.CTkFrame(
            self, fg_color=COLORS["surface_alt"],
            corner_radius=BTN_RADIUS, border_width=1, border_color=COLORS["border"],
        )
        note_frame.pack(fill="x", padx=CONTENT_PADX, pady=16)
        ctk.CTkLabel(
            note_frame,
            text=(
                "Lưu ý: Webcam sẽ nhận diện khuôn mặt liên tục.\n"
                "Nhấn Q trong cửa sổ webcam để kết thúc."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface_alt"],
            justify="left",
        ).pack(padx=16, pady=12, anchor="w")

    def _start_recognition(self):
        if self._running:
            self.toast.show("Webcam đang chạy, hãy đóng cửa sổ camera trước.", "warning")
            return

        subject = self.var_subject.get().strip()
        self._set_status("Đang mở webcam...", COLORS["warning"])
        self.btn_start.configure(state="disabled")
        self._running = True

        def _run():
            result = run_face_attendance(subject)
            def _update_ui():
                self._running = False
                self.btn_start.configure(state="normal")
                if result:
                    self._set_status("Đã kết thúc phiên điểm danh.", COLORS["success"])
                    self.toast.show("Phiên điểm danh kết thúc.", "success")
                else:
                    self._set_status(
                        "Không thể mở webcam hoặc chưa có dữ liệu khuôn mặt.",
                        COLORS["danger"],
                    )
                    self.toast.show("Không thể bắt đầu nhận diện.", "error")
            self.after(0, _update_ui)
        threading.Thread(target=_run, daemon=True).start()

    def _set_status(self, text, color):
        self.after(0, lambda: self.status_lbl.configure(text=text, text_color=color))

# ──────────────────────────────────────────────
# Panel: Dashboard tổng quan
# ──────────────────────────────────────────────

class AttendancePanel(ctk.CTkFrame):
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self.stat_labels = {}
        self.stat_cards  = {}
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=CONTENT_PADX, pady=(22, 4))
        title_box = ctk.CTkFrame(header, fg_color=COLORS["bg"])
        title_box.pack(side="left", anchor="w")
        ctk.CTkLabel(
            title_box, text="Tổng quan",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Theo dõi số lượng đi học, vắng và điểm danh theo lớp hành chính hoặc nội dung học tập.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _flat_btn(
            header, "🔄  Tải lại",
            command=self.load_data,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(side="right", pady=4)
        _separator(self).pack(fill="x", padx=CONTENT_PADX, pady=(8, 0))

        content = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        content.pack(fill="both", expand=True)

        self.dashboard_table_rows = 7

        card_row = ctk.CTkFrame(content, fg_color=COLORS["bg"])
        card_row.pack(fill="x", padx=CONTENT_PADX, pady=(10, 8))

        self._build_stat_card(card_row, "Tổng sinh viên", "total_students", "🎓", COLORS["accent"])
        self._build_stat_card(card_row, "Đã điểm danh hôm nay", "today_attendance", "✅", COLORS["success"])
        self._build_stat_card(card_row, "Chưa điểm danh hôm nay", "not_attended_today", "⏳", COLORS["warning"])
        self._build_stat_card(card_row, "Tổng lượt điểm danh", "total_attendance", "🧾", COLORS["danger"], last=True)

        recent_card = _card(content)
        recent_card.pack(fill="x", padx=CONTENT_PADX, pady=(0, 8))
        ctk.CTkLabel(
            recent_card, text="Điểm danh gần đây",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w", padx=16, pady=(14, 8))

        cols   = ("date", "time", "student_id", "full_name", "class_name", "subject")
        heads  = ("Ngày", "Giờ", "Mã sinh viên", "Họ và tên", "Lớp hành chính", "Môn / Lớp học phần")
        widths = [110, 90, 130, 220, 150, 220]
        aligns = ["center", "center", "center", "w", "center", "w"]
        self.recent_table = StyledTable(
            recent_card, columns=cols, headings=heads,
            col_widths=widths, col_alignments=aligns, rows=self.dashboard_table_rows,
        )
        self.recent_table.pack(fill="x", padx=14, pady=(0, 14))

        stats_row = ctk.CTkFrame(content, fg_color=COLORS["bg"])
        stats_row.pack(fill="x", padx=CONTENT_PADX, pady=(0, 16))
        stats_row.grid_columnconfigure(0, weight=1, uniform="dashboard_stats")
        stats_row.grid_columnconfigure(1, weight=1, uniform="dashboard_stats")

        class_card = _card(stats_row)
        class_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ctk.CTkLabel(
            class_card, text="Thống kê theo lớp hành chính",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w", padx=16, pady=(14, 8))

        cols   = ("class_name", "total_students", "attended_today", "not_attended")
        heads  = ("Lớp hành chính", "Tổng sinh viên", "Đã điểm danh", "Chưa điểm danh")
        widths = [200, 130, 130, 130]
        aligns = ["w", "center", "center", "center"]
        self.class_table = StyledTable(
            class_card, columns=cols, headings=heads,
            col_widths=widths, col_alignments=aligns, rows=self.dashboard_table_rows,
        )
        self.class_table.pack(fill="x", padx=14, pady=(0, 14))

        subject_card = _card(stats_row)
        subject_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(
            subject_card, text="Thống kê theo môn / lớp học phần",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w", padx=16, pady=(14, 8))

        cols   = ("subject", "total_students", "attended_today", "not_attended")
        heads  = ("Môn / Lớp học phần", "Tổng sinh viên", "Đã điểm danh", "Chưa điểm danh")
        widths = [230, 120, 120, 120]
        aligns = ["w", "center", "center", "center"]
        self.subject_table = StyledTable(
            subject_card, columns=cols, headings=heads,
            col_widths=widths, col_alignments=aligns, rows=self.dashboard_table_rows,
        )
        self.subject_table.pack(fill="x", padx=14, pady=(0, 14))

        self.load_data()

    def _build_stat_card(self, parent, title, key, icon, color, last=False):
        card = _card(parent)
        card.pack(side="left", fill="x", expand=True, padx=(0, 0 if last else 12))
        self.stat_cards[key] = card

        top_row = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        top_row.pack(fill="x", padx=16, pady=(14, 0), anchor="w")

        badge = ctk.CTkLabel(
            top_row, text=icon,
            font=ctk.CTkFont(family="Segoe UI Emoji", size=18),
            text_color=COLORS["on_accent"], fg_color=color,
            width=36, height=36, corner_radius=8,
        )
        badge.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_row, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
            anchor="w", justify="left", wraplength=160,
        ).pack(side="left", fill="x", expand=True)

        value_lbl = ctk.CTkLabel(
            card, text="0",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        )
        value_lbl.pack(anchor="w", padx=16, pady=(8, 16))

        self.stat_labels[key] = value_lbl

    def load_data(self):
        total_students = get_total_students()
        today_count = get_today_attendance_count()
        not_attended_today = get_not_attended_today_count()
        total_attendance = get_total_attendance_count()

        self.stat_labels["total_students"].configure(text=str(total_students))
        self.stat_labels["today_attendance"].configure(text=str(today_count))
        self.stat_labels["not_attended_today"].configure(text=str(not_attended_today))
        self.stat_labels["total_attendance"].configure(text=str(total_attendance))

        self.recent_table.clear()
        for r in get_recent_attendance(limit=self.dashboard_table_rows):
            self.recent_table.insert((
                r.get("date", ""),
                r.get("time", ""),
                r.get("student_id", ""),
                r.get("full_name", ""),
                r.get("class_name", "") or "—",
                r.get("subject", "") or "—",
            ))

        self.class_table.clear()
        for r in get_class_statistics():
            total = r.get("total_students", 0)
            attended = r.get("attended_today", 0)
            not_attended = max(total - attended, 0)
            self.class_table.insert((
                r.get("class_name", "") or "—",
                total,
                attended,
                not_attended,
            ))

        self.subject_table.clear()
        today = datetime.now().strftime("%Y-%m-%d")
        active_student_ids = {
            s.get("student_id", "") for s in get_all_students()
        }
        subject_stats = {}

        for r in get_all_attendance():
            subject = r.get("subject", "") or "Không có nội dung"
            student_id = r.get("student_id", "")
            if not student_id or student_id not in active_student_ids:
                continue

            if subject not in subject_stats:
                subject_stats[subject] = {
                    "students": set(),
                    "attended_today": set(),
                }

            subject_stats[subject]["students"].add(student_id)
            if r.get("date", "") == today:
                subject_stats[subject]["attended_today"].add(student_id)

        sorted_subjects = sorted(
            subject_stats.items(),
            key=lambda item: (len(item[1]["attended_today"]), len(item[1]["students"]), item[0]),
            reverse=True,
        )

        for subject, data in sorted_subjects:
            total = len(data["students"])
            attended = len(data["attended_today"])
            not_attended = max(total - attended, 0)
            self.subject_table.insert((
                subject,
                total,
                attended,
                not_attended,
            ))

# ──────────────────────────────────────────────
# Panel: Quản lý sinh viên
# ──────────────────────────────────────────────

class StudentsPanel(ctk.CTkFrame):
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=CONTENT_PADX, pady=(26, 6))
        title_box = ctk.CTkFrame(header, fg_color=COLORS["bg"])
        title_box.pack(side="left", anchor="w")
        ctk.CTkLabel(
            title_box, text="Quản lý sinh viên",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Tìm kiếm, cập nhật thông tin, xem ảnh và lịch sử điểm danh của sinh viên.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _flat_btn(
            header, "🔄  Tải lại",
            command=self.load_data,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(side="right", pady=4)
        _separator(self).pack(fill="x", padx=CONTENT_PADX, pady=(10, 0))

        search_row = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        search_row.pack(fill="x", padx=CONTENT_PADX, pady=(12, 6))

        self.var_search = tk.StringVar()

        ctk.CTkLabel(
            search_row, text="Tìm kiếm",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["bg"],
        ).pack(side="left", padx=(0, 12))

        self.search_entry = _entry(search_row, textvariable=self.var_search, width=320)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda e: self.load_data())

        _flat_btn(
            search_row, "Tìm",
            command=self.load_data,
            color=COLORS["accent"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(side="left", padx=(12, 8))

        _flat_btn(
            search_row, "Xóa lọc",
            command=self._clear_search,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            self, text="...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        )
        self.count_lbl.pack(anchor="w", padx=CONTENT_PADX, pady=(0, 6))

        cols   = ("student_id", "full_name", "class_name", "gender", "created_at")
        heads  = ("Mã sinh viên", "Họ và tên", "Lớp hành chính", "Giới tính", "Ngày đăng ký")
        widths = [150, 260, 150, 120, 180]
        aligns = ["center", "w", "center", "center", "center"]
        self.table = StyledTable(
            self, columns=cols, headings=heads,
            col_widths=widths, col_alignments=aligns,
        )
        self.table.pack(fill="both", expand=True, padx=CONTENT_PADX, pady=(0, 16))

        btn_row = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        btn_row.pack(fill="x", padx=CONTENT_PADX, pady=(0, 24))

        _flat_btn(
            btn_row, "✏️ Sửa thông tin",
            command=self._edit_selected,
            color=COLORS["accent"],
        ).pack(side="left", padx=(0, 10))

        _flat_btn(
            btn_row, "📸  Chụp lại ảnh",
            command=self._update_face_selected,
            color=COLORS["warning"],
            text_color=COLORS["on_accent"],
        ).pack(side="left", padx=(0, 10))

        _flat_btn(
            btn_row, "🖼  Xem ảnh",
            command=self._show_image_selected,
            color=COLORS["accent"],
            text_color=COLORS["on_accent"],
        ).pack(side="left", padx=(0, 10))

        _flat_btn(
            btn_row, "📜  Lịch sử điểm danh",
            command=self._show_history_selected,
            color=COLORS["success"],
            text_color=COLORS["on_accent"],
        ).pack(side="left", padx=(0, 10))

        _flat_btn(
            btn_row, "🗑  Xóa",
            command=self._delete_selected,
            color=COLORS["danger"],
        ).pack(side="left")

        self.load_data()

    def load_data(self):
        keyword = self.var_search.get().strip() if hasattr(self, "var_search") else ""

        if keyword:
            students = search_students(keyword)
        else:
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

        if keyword:
            self.count_lbl.configure(text=f"{len(students)} kết quả tìm kiếm.")
        else:
            self.count_lbl.configure(text=f"{len(students)} sinh viên đang hoạt động.")

    def _clear_search(self):
        self.var_search.set("")
        self.load_data()

    def _get_selected_student(self):
        vals = self.table.selected_values()
        if not vals:
            self.toast.show("Hãy chọn một sinh viên trong danh sách.", "warning")
            return None
        return vals

    def _edit_selected(self):
        vals = self._get_selected_student()
        if not vals:
            return

        sid = vals[0]
        student = get_student(sid)

        if not student:
            self.toast.show("Không tìm thấy sinh viên.", "error")
            return

        win = ctk.CTkToplevel(self)
        win.title("Sửa thông tin sinh viên")
        win.geometry("460x380")
        win.resizable(False, False)
        win.configure(fg_color=COLORS["bg"])
        win.transient(self.winfo_toplevel())
        win.grab_set()

        card = _card(win)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card, text="Sửa thông tin sinh viên",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w", padx=24, pady=(20, 14))

        form = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        form.pack(fill="x", padx=24)

        var_name   = tk.StringVar(value=student.get("full_name", ""))
        var_class  = tk.StringVar(value=student.get("class_name", "") or "")
        var_gender = tk.StringVar(value=student.get("gender", "") or "Nam")

        rows = [
            ("Mã sinh viên", None),
            ("Họ và tên", var_name),
            ("Lớp hành chính", var_class),
        ]

        for label_text, var in rows:
            row = ctk.CTkFrame(form, fg_color=COLORS["surface"])
            row.pack(fill="x", pady=6)
            ctk.CTkLabel(
                row, text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
                width=110, anchor="w",
            ).pack(side="left")
            if var is None:
                ctk.CTkLabel(
                    row, text=sid,
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color=COLORS["text"], fg_color=COLORS["surface"],
                    anchor="w",
                ).pack(side="left")
            else:
                _entry(row, textvariable=var, width=250).pack(side="left")

        gender_row = ctk.CTkFrame(form, fg_color=COLORS["surface"])
        gender_row.pack(fill="x", pady=6)
        ctk.CTkLabel(
            gender_row, text="Giới tính",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=110, anchor="w",
        ).pack(side="left")
        ctk.CTkSegmentedButton(
            gender_row,
            values=["Nam", "Nữ"],
            variable=var_gender,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=COLORS["surface_alt"],
            selected_color=COLORS["accent"],
            selected_hover_color=_darken(COLORS["accent"], 24),
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        ).pack(side="left")

        btn_row = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        btn_row.pack(fill="x", padx=24, pady=(20, 20))

        def _save():
            full_name = var_name.get().strip()
            class_name = var_class.get().strip()
            gender = var_gender.get().strip()

            if not full_name:
                self.toast.show("Vui lòng nhập họ tên.", "warning")
                return

            if update_student(sid, full_name, class_name, gender):
                win.destroy()
                self.toast.show("Đã cập nhật thông tin sinh viên.", "success")
                self.load_data()
            else:
                self.toast.show("Không thể cập nhật sinh viên.", "error")

        _flat_btn(
            btn_row, "Lưu thay đổi",
            command=_save,
            color=COLORS["success"],
        ).pack(side="left", padx=(0, 10))

        _flat_btn(
            btn_row, "Hủy",
            command=win.destroy,
            color=COLORS["surface_alt"],
            text_color=COLORS["text_dim"],
        ).pack(side="left")

    def _update_face_selected(self):
        vals = self._get_selected_student()
        if not vals:
            return
        sid = vals[0]
        name = vals[1]
        confirm = messagebox.askyesno(
            "Cập nhật khuôn mặt",f"Bật webcam để chụp lại dữ liệu khuôn mặt cho:\n\n  {name} ({sid})?"
        )
        if not confirm:
            return

        self.toast.show("Đang mở camera...", "info")
        def _run():
            success, msg = update_face_from_ui(sid)
            def _update_ui():
                if success:
                    self.toast.show(msg, "success")
                else:
                    self.toast.show(msg, "error")
            self.after(0, _update_ui)
        threading.Thread(target=_run, daemon=True).start()

    def _show_image_selected(self):
        vals = self._get_selected_student()
        if not vals:
            return

        sid  = vals[0]
        name = vals[1]
        image_path = self._find_student_image(sid)

        if not image_path:
            self.toast.show("Không tìm thấy ảnh sinh viên.", "warning")
            return

        win = ctk.CTkToplevel(self)
        win.title("Ảnh sinh viên")
        win.geometry("600x540")
        win.configure(fg_color=COLORS["bg"])
        win.transient(self.winfo_toplevel())
        win.grab_set()

        card = _card(win)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card, text=f"{name} ({sid})",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="center", padx=24, pady=(20, 14))

        try:
            img = Image.open(image_path)
            img.thumbnail((500, 400))
            photo = ImageTk.PhotoImage(img)

            img_lbl = tk.Label(card, image=photo, bg=COLORS["surface"])
            img_lbl.image = photo
            img_lbl.pack(padx=24, pady=(0, 24))
        except Exception:
            win.destroy()
            self.toast.show("Không thể mở ảnh sinh viên.", "error")

    def _find_student_image(self, student_id):
        student = get_student(student_id)

        if student:
            image_path = student.get("image_path", "") or ""
            if image_path and os.path.exists(image_path):
                return image_path

        face_dir = os.path.join(FACES_DIR, student_id)
        if os.path.isdir(face_dir):
            for filename in os.listdir(face_dir):
                if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    return os.path.join(face_dir, filename)

        return None

    def _show_history_selected(self):
        vals = self._get_selected_student()
        if not vals:
            return

        sid  = vals[0]
        name = vals[1]
        records = get_attendance_by_student(sid)

        win = ctk.CTkToplevel(self)
        win.title("Lịch sử điểm danh")
        win.geometry("820x500")
        win.configure(fg_color=COLORS["bg"])
        win.transient(self.winfo_toplevel())
        win.grab_set()

        header = ctk.CTkFrame(win, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(
            header, text=f"Lịch sử điểm danh - {name} ({sid})",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text=f"{len(records)} lượt điểm danh",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(4, 0))

        cols   = ("date", "time", "subject", "status", "note")
        heads  = ("Ngày", "Giờ", "Môn / Lớp học phần", "Trạng thái", "Ghi chú")
        widths = [120, 100, 200, 120, 240]
        aligns = ["center", "center", "w", "center", "w"]
        table = StyledTable(
            win, columns=cols, headings=heads,
            col_widths=widths, col_alignments=aligns,
        )
        table.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        for r in records:
            table.insert((
                r.get("date", ""),
                r.get("time", ""),
                r.get("subject", "") or "—",
                r.get("status", "") or "—",
                r.get("note", "") or "—",
            ))

    def _delete_selected(self):
        vals = self._get_selected_student()
        if not vals:
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

        deleted = delete_student(sid)
        if deleted:
            remove_encoding(sid)
            self.toast.show(f"Đã xóa: {name} ({sid})", "success")
            self.load_data()
        else:
            self.toast.show("Không thể xóa. Sinh viên có thể đã bị xóa rồi.", "error")

# ──────────────────────────────────────────────
# Panel: Xuất báo cáo
# ──────────────────────────────────────────────

class ReportPanel(ctk.CTkFrame):
    def __init__(self, parent, toast, **kw):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0, **kw)
        self.toast = toast
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=CONTENT_PADX, pady=(26, 6))
        ctk.CTkLabel(
            header, text="Xuất báo cáo",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["bg"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Xuất dữ liệu điểm danh ra file báo cáo.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", pady=(2, 0))
        _separator(self).pack(fill="x", padx=CONTENT_PADX, pady=(10, 0))

        card = _card(self)
        card.pack(fill="x", padx=CONTENT_PADX, pady=18)
        inner = ctk.CTkFrame(card, fg_color=COLORS["surface"])
        inner.pack(padx=22, pady=18, fill="x")

        ctk.CTkLabel(
            inner, text="Tùy chọn xuất báo cáo",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text="Chọn phạm vi dữ liệu và định dạng file cần xuất.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="w", pady=(4, 16))

        self.var_report_type = tk.StringVar(value="Toàn bộ")
        self.var_file_format = tk.StringVar(value="CSV")
        self.var_report_date = tk.StringVar()
        self.var_start_date  = tk.StringVar()
        self.var_end_date    = tk.StringVar()

        report_type_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        report_type_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            report_type_row, text="Loại báo cáo",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=130, anchor="w",
        ).pack(side="left")
        self.report_type_segment = ctk.CTkSegmentedButton(
            report_type_row,
            values=["Toàn bộ", "Theo ngày", "Khoảng ngày"],
            variable=self.var_report_type,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=lambda _: self._update_report_inputs(),
            fg_color=COLORS["surface_alt"],
            selected_color=COLORS["accent"],
            selected_hover_color=_darken(COLORS["accent"], 24),
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.report_type_segment.pack(side="left")

        format_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        format_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            format_row, text="Định dạng",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=130, anchor="w",
        ).pack(side="left")
        self.format_segment = ctk.CTkSegmentedButton(
            format_row,
            values=["CSV", "Excel"],
            variable=self.var_file_format,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=COLORS["surface_alt"],
            selected_color=COLORS["accent"],
            selected_hover_color=_darken(COLORS["accent"], 24),
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.format_segment.pack(side="left")

        date_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        date_row.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            date_row, text="Ngày",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=130, anchor="w",
        ).pack(side="left")
        self.date_entry = _entry(date_row, textvariable=self.var_report_date, width=200)
        self.date_entry.pack(side="left")
        ctk.CTkLabel(
            date_row, text="YYYY-MM-DD",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(side="left", padx=(12, 0))

        range_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        range_row.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            range_row, text="Khoảng ngày",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"], fg_color=COLORS["surface"],
            width=130, anchor="w",
        ).pack(side="left")
        self.start_date_entry = _entry(range_row, textvariable=self.var_start_date, width=160)
        self.start_date_entry.pack(side="left")
        ctk.CTkLabel(
            range_row, text="đến",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(side="left", padx=10)
        self.end_date_entry = _entry(range_row, textvariable=self.var_end_date, width=160)
        self.end_date_entry.pack(side="left")

        btn_row = ctk.CTkFrame(inner, fg_color=COLORS["surface"])
        btn_row.pack(anchor="w", pady=(4, 0))
        _flat_btn(
            btn_row, "Xuất báo cáo",
            command=self._export_report,
            color=COLORS["success"],
        ).pack(side="left")

        self._update_report_inputs()

        _separator(self).pack(fill="x", padx=CONTENT_PADX, pady=(0, 14))
        ctk.CTkLabel(
            self, text="Nhật ký xuất báo cáo:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_muted"], fg_color=COLORS["bg"],
        ).pack(anchor="w", padx=CONTENT_PADX)

        self.log_text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["surface"],
            text_color=COLORS["text_dim"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=CARD_RADIUS,
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=CONTENT_PADX, pady=(6, 24))

    def _set_entry_state(self, entry, enabled):
        if enabled:
            entry.configure(
                state="normal",
                fg_color=COLORS["surface"],
                text_color=COLORS["text"],
                border_color=COLORS["border"],
            )
        else:
            entry.configure(
                state="disabled",
                fg_color=COLORS["surface_alt"],
                text_color=COLORS["text_muted"],
                border_color=COLORS["border"],
            )

    def _update_report_inputs(self):
        report_type = self.var_report_type.get()
        self._set_entry_state(self.date_entry, report_type == "Theo ngày")
        self._set_entry_state(self.start_date_entry, report_type == "Khoảng ngày")
        self._set_entry_state(self.end_date_entry, report_type == "Khoảng ngày")

    def _log(self, msg, color=None):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _export_report(self):
        report_type_text = self.var_report_type.get()
        file_format_text = self.var_file_format.get()
        date             = self.var_report_date.get().strip()
        start_date       = self.var_start_date.get().strip()
        end_date         = self.var_end_date.get().strip()

        report_type_map = {
            "Toàn bộ": "all",
            "Theo ngày": "date",
            "Khoảng ngày": "range",
        }
        file_format_map = {
            "CSV": "csv",
            "Excel": "excel",
        }

        report_type = report_type_map.get(report_type_text, "all")
        file_format = file_format_map.get(file_format_text, "csv")

        if report_type == "date" and not date:
            self.toast.show("Vui lòng nhập ngày cần xuất báo cáo.", "warning")
            return

        if report_type == "range" and (not start_date or not end_date):
            self.toast.show("Vui lòng nhập đầy đủ ngày bắt đầu và ngày kết thúc.", "warning")
            return

        if report_type == "all":
            self._log(f"Đang xuất toàn bộ dữ liệu ra {file_format_text}...")
        elif report_type == "date":
            self._log(f"Đang xuất dữ liệu ngày {date} ra {file_format_text}...")
        else:
            self._log(f"Đang xuất dữ liệu từ {start_date} đến {end_date} ra {file_format_text}...")

        def _run():
            success, message = export_attendance_report(
                report_type=report_type,
                file_format=file_format,
                date=date,
                start_date=start_date,
                end_date=end_date,
            )
            self.after(0, lambda: self._on_export_done(success, message))

        threading.Thread(target=_run, daemon=True).start()

    def _on_export_done(self, success, message):
        if success:
            self._log(f"Thành công: {message}")
            self.toast.show("Xuất báo cáo thành công!", "success")
        else:
            self._log(f"Lỗi: {message}")
            self.toast.show(message, "error")

# ──────────────────────────────────────────────
# Cửa sổ chính: FaceAttendanceApp
# ──────────────────────────────────────────────

class FaceAttendanceApp(ctk.CTk):
    def __init__(self):
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
        self._show_panel("attendance")

    def _setup_window(self):
        self.title("Face Attendance System")
        self.geometry("1180x820")
        self.minsize(1000, 720)
        self.configure(fg_color=COLORS["bg"])
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _build_layout(self):
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=0,
            width=SIDEBAR_WIDTH,
            border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = ctk.CTkFrame(
            self, fg_color=COLORS["bg"], corner_radius=0,
        )
        self.content_area.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_panels()

    def _build_sidebar(self):
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface"])
        logo_frame.pack(fill="x", pady=(24, 8))
        ctk.CTkLabel(
            logo_frame, text="Face Attendance System",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"], fg_color=COLORS["surface"],
            anchor="w", justify="left", wraplength=190,
        ).pack(padx=20, anchor="w")
        ctk.CTkLabel(
            logo_frame, text="v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(padx=20, anchor="w", pady=(2, 0))

        _separator(self.sidebar, bg=COLORS["border"]).pack(fill="x", padx=16, pady=10)

        nav_items = [
            ("attendance",  "📋", "Tổng quan"),
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
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_btns[key] = btn

        ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface"]).pack(
            fill="both", expand=True,
        )

        _separator(self.sidebar, bg=COLORS["border"]).pack(fill="x", padx=16, pady=(10, 12))

        theme_row = ctk.CTkFrame(self.sidebar, fg_color=COLORS["surface"])
        theme_row.pack(anchor="center", pady=(0, 12))
        theme_row.grid_columnconfigure(0, minsize=32)
        theme_row.grid_columnconfigure(2, minsize=32)

        ctk.CTkLabel(
            theme_row, text="☀️",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=14),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
            width=32, anchor="center",
        ).grid(row=0, column=0, padx=(0, 8))

        self.theme_switch = ctk.CTkSwitch(
            theme_row,
            text="",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light",
            width=48,
            height=24,
            progress_color=COLORS["accent"],
            button_color="#FFFFFF",
            button_hover_color=COLORS["surface_alt"],
            fg_color=COLORS["border"],
        )
        self.theme_switch.grid(row=0, column=1)

        ctk.CTkLabel(
            theme_row, text="🌙",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=14),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
            width=32, anchor="center",
        ).grid(row=0, column=2, padx=(8, 0))

        if self._current_mode == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        _separator(self.sidebar, bg=COLORS["border"]).pack(fill="x", padx=16, pady=(0, 0))
        footer_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["surface"],
            height=68,
        )
        footer_frame.pack(fill="x", padx=16, pady=(0, 14))
        footer_frame.pack_propagate(False)

        footer_inner = ctk.CTkFrame(footer_frame, fg_color=COLORS["surface"])
        footer_inner.pack(expand=True)
        ctk.CTkLabel(
            footer_inner, text="Python · OpenCV · SQLite",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"], fg_color=COLORS["surface"],
        ).pack(anchor="center")

    def _build_panels(self):
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
        for k, panel in self._panels.items():
            panel.pack_forget()
        for k, btn in self._nav_btns.items():
            btn.set_active(k == key)

        panel = self._panels[key]
        panel.pack(fill="both", expand=True)

        if hasattr(panel, "load_data"):
            panel.load_data()

    def _toggle_theme(self):
        new_mode = "dark" if self._current_mode == "light" else "light"
        _apply_theme(new_mode)
        self._current_mode = new_mode

        self._active_panel_key = next(
            (k for k, btn in self._nav_btns.items() if btn._active),
            "attendance",
        )

        self.configure(fg_color=COLORS["bg"])
        self.content_area.configure(fg_color=COLORS["bg"])
        self.sidebar.configure(fg_color=COLORS["surface"])

        self._rebuild_all()

    def _rebuild_all(self):
        active_key = getattr(self, "_active_panel_key", "attendance")

        for child in self.sidebar.winfo_children():
            child.destroy()
        self._nav_btns.clear()
        self._build_sidebar()

        for child in self.content_area.winfo_children():
            child.destroy()
        self._panels.clear()
        self._build_panels()

        self._show_panel(active_key)

# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def run_app():
    app = FaceAttendanceApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
