import os
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk


def _format_size(size_bytes: int) -> str:
    """Format bytes into readable units."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


class FloatingOutputWidget:
    _instance = None

    @classmethod
    def get_instance(cls, parent=None):
        if cls._instance is None or not cls._instance.is_alive():
            cls._instance = cls(parent)
        return cls._instance

    def __init__(self, parent=None):
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Preview & Output")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.98)

        self.width = 400
        self.height = 320

        # Position directly above the bottom-right input bar
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        pos_x = screen_w - self.width - 24
        pos_y = screen_h - self.height - 118
        self.window.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")
        self.window.configure(bg="#F8FAFC")

        self._offset_x = 0
        self._offset_y = 0
        self._photo_cache = None

        self._build_ui()

    def is_alive(self):
        try:
            return self.window.winfo_exists()
        except Exception:
            return False

    def _build_ui(self):
        # Card container with clean border
        self.card = tk.Frame(
            self.window,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            bd=0
        )
        self.card.pack(fill="both", expand=True, padx=1, pady=1)

        # Header bar
        self.header = tk.Frame(self.card, bg="#FFFFFF", height=32)
        self.header.pack(fill="x", padx=10, pady=(8, 4))

        self.title_label = tk.Label(
            self.header,
            text="Result Preview",
            font=("Segoe UI", 9, "bold"),
            fg="#0F172A",
            bg="#FFFFFF"
        )
        self.title_label.pack(side="left")

        # Close button
        self.close_btn = tk.Label(
            self.header,
            text="✕",
            font=("Segoe UI", 8, "bold"),
            fg="#94A3B8",
            bg="#FFFFFF",
            cursor="hand2"
        )
        self.close_btn.pack(side="right")
        self.close_btn.bind("<Button-1>", lambda e: self.hide())

        # Dragging
        for w in (self.header, self.title_label, self.card):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

        # Dynamic content container
        self.content_frame = tk.Frame(self.card, bg="#FFFFFF")
        self.content_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

    def _start_drag(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _do_drag(self, event):
        x = self.window.winfo_pointerx() - self._offset_x
        y = self.window.winfo_pointery() - self._offset_y
        self.window.geometry(f"+{x}+{y}")

    def clear(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show(self):
        self.window.deiconify()
        self.window.lift()

    def hide(self):
        self.window.withdraw()

    # --- Render: Screenshot / Image Preview ---
    def render_image(self, file_path: str, caption: str = "Screenshot"):
        self.clear()
        self.title_label.config(text=f"🖼️ {caption}")

        if not os.path.exists(file_path):
            self.render_text(f"File not found: {file_path}")
            return

        size_str = _format_size(os.path.getsize(file_path))

        try:
            # Native PhotoImage loader
            self._photo_cache = tk.PhotoImage(file=file_path)
            w = self._photo_cache.width()
            h = self._photo_cache.height()

            # Preview box
            img_container = tk.Frame(self.content_frame, bg="#F1F5F9", bd=1, relief="solid")
            img_container.pack(fill="both", expand=True, padx=4, pady=4)

            img_label = tk.Label(img_container, image=self._photo_cache, bg="#F1F5F9")
            img_label.pack(fill="both", expand=True)

            # Metadata footer
            meta_label = tk.Label(
                self.content_frame,
                text=f"{os.path.basename(file_path)} • {w}x{h} px • {size_str}",
                font=("Segoe UI", 8),
                fg="#64748B",
                bg="#FFFFFF"
            )
            meta_label.pack(side="bottom", fill="x")
        except Exception:
            self.render_text(f"Image saved: {file_path}\nSize: {size_str}")

        self.show()

    # --- Render: File & Folder Explorer (With Name, Icon & Size) ---
    def render_file_list(self, title: str, items: list, base_dir: str = "."):
        self.clear()
        self.title_label.config(text=f"📁 {title} ({len(items)})")

        canvas = tk.Canvas(self.content_frame, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#F8FAFC")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for item in items:
            name = str(item)
            full_path = os.path.join(base_dir, name) if os.path.exists(os.path.join(base_dir, name)) else name

            is_dir = os.path.isdir(full_path) if os.path.exists(full_path) else not ("." in name and not name.startswith("."))
            icon = "📁" if is_dir else "📄"

            # Resolve file size if path exists
            if os.path.exists(full_path) and not is_dir:
                size_str = _format_size(os.path.getsize(full_path))
            else:
                size_str = "Folder" if is_dir else ""

            row = tk.Frame(
                scroll_frame,
                bg="#FFFFFF",
                highlightthickness=1,
                highlightbackground="#E2E8F0"
            )
            row.pack(fill="x", padx=4, pady=2)

            tk.Label(row, text=icon, font=("Segoe UI", 10), bg="#FFFFFF").pack(side="left", padx=(6, 4))
            tk.Label(
                row,
                text=name,
                font=("Segoe UI", 9),
                fg="#0F172A",
                bg="#FFFFFF",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, pady=4)

            if size_str:
                tk.Label(
                    row,
                    text=size_str,
                    font=("Segoe UI", 8),
                    fg="#64748B",
                    bg="#FFFFFF"
                ).pack(side="right", padx=6)

        self.show()

    # --- Render: Time / Date Widget ---
    def render_datetime(self, result_value=None):
        self.clear()
        self.title_label.config(text="⏰ Date & Time")

        now = datetime.now()
        current_time = now.strftime("%I:%M:%S %p")
        current_date = now.strftime("%A, %B %d, %Y")

        container = tk.Frame(self.content_frame, bg="#F0FDF4", bd=0)
        container.pack(fill="both", expand=True, padx=6, pady=6)

        tk.Label(
            container,
            text=current_time,
            font=("Segoe UI", 20, "bold"),
            fg="#059669",
            bg="#F0FDF4"
        ).pack(expand=True, pady=(20, 2))

        tk.Label(
            container,
            text=current_date,
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="#F0FDF4"
        ).pack(expand=True, pady=(0, 20))

        if result_value:
            tk.Label(
                container,
                text=f"Raw: {result_value}",
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#F0FDF4"
            ).pack(side="bottom", pady=4)

        self.show()

    # --- Render: Generic Text / Calculation ---
    def render_text(self, text: str, title: str = "Result"):
        self.clear()
        self.title_label.config(text=f"ℹ️ {title}")

        text_box = tk.Text(
            self.content_frame,
            bg="#F8FAFC",
            fg="#0F172A",
            font=("Segoe UI", 10),
            bd=0,
            wrap="word",
            padx=10,
            pady=10
        )
        text_box.insert("1.0", str(text))
        text_box.config(state="disabled")
        text_box.pack(fill="both", expand=True)

        self.show()