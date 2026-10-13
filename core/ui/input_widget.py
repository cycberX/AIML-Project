import tkinter as tk


class FloatingInputWidget:
    def __init__(self, on_submit=None):
        self.on_submit = on_submit

        self.root = tk.Tk()
        self.root.title("Quick Input")

        # Window properties: Frameless, Always on Top
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.98)

        # Transparent canvas background on Windows
        self.bg_color = "#F0F2F5"
        self.root.configure(bg=self.bg_color)
        try:
            self.root.wm_attributes("-transparentcolor", self.bg_color)
        except Exception:
            pass

        self.width = 400
        self.height = 46

        # Position at bottom-right corner
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - self.width - 24
        pos_y = screen_h - self.height - 65
        self.root.geometry(f"{self.width}x{self.height}+{pos_x}+{pos_y}")

        self._offset_x = 0
        self._offset_y = 0
        self.history = []
        self.history_index = -1

        self._build_ui()

    def _draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=20, **kwargs):
        """Draws a smooth polygon with exact rounded corners."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _build_ui(self):
        # Canvas host for rounded borders
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Draw outer green border (radius 20)
        self._draw_rounded_rectangle(
            self.canvas, 2, 2, self.width - 2, self.height - 2,
            radius=20, fill="#10B981"
        )
        # Draw inner white card body
        self._draw_rounded_rectangle(
            self.canvas, 4, 4, self.width - 4, self.height - 4,
            radius=18, fill="#FFFFFF"
        )

        # Inner container for inputs
        self.content_frame = tk.Frame(self.canvas, bg="#FFFFFF")
        self.canvas.create_window(
            self.width // 2, self.height // 2,
            window=self.content_frame,
            width=self.width - 20,
            height=self.height - 12
        )

        # Drag handle icon
        self.grip = tk.Label(
            self.content_frame, text="⋮⋮",
            font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#FFFFFF",
            cursor="fleur"
        )
        self.grip.pack(side="left", padx=(4, 2))
        self.grip.bind("<Button-1>", self._start_drag)
        self.grip.bind("<B1-Motion>", self._do_drag)

        # Icon
        self.icon = tk.Label(
            self.content_frame, text="✦",
            font=("Segoe UI", 11, "bold"), fg="#10B981", bg="#FFFFFF"
        )
        self.icon.pack(side="left", padx=(2, 6))

        # Input field
        self.entry = tk.Entry(
            self.content_frame,
            bg="#FFFFFF",
            fg="#0F172A",
            insertbackground="#10B981",
            bd=0,
            font=("Segoe UI", 10),
            relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=2, padx=(2, 4))
        self.entry.bind("<Return>", lambda e: self._submit())
        self.entry.bind("<Up>", self._prev_history)
        self.entry.bind("<Down>", self._next_history)
        self.entry.focus_set()

        # Submit button
        self.send_btn = tk.Label(
            self.content_frame, text="↵",
            font=("Segoe UI", 11, "bold"), fg="#10B981", bg="#ECFDF5",
            padx=6, pady=0, cursor="hand2"
        )
        self.send_btn.pack(side="right", padx=(2, 6))
        self.send_btn.bind("<Button-1>", lambda e: self._submit())

        # Close button
        self.close_btn = tk.Label(
            self.content_frame, text="✕",
            font=("Segoe UI", 8, "bold"), fg="#94A3B8", bg="#FFFFFF",
            cursor="hand2"
        )
        self.close_btn.pack(side="right", padx=(0, 2))
        self.close_btn.bind("<Button-1>", lambda e: self.root.destroy())

    def _start_drag(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _do_drag(self, event):
        x = self.root.winfo_pointerx() - self._offset_x
        y = self.root.winfo_pointery() - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def _submit(self):
        query = self.entry.get().strip()
        if not query:
            return

        self.history.append(query)
        self.history_index = len(self.history)
        self.entry.delete(0, tk.END)

        if callable(self.on_submit):
            self.on_submit(query)

    def _prev_history(self, event):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.history[self.history_index])
        return "break"

    def _next_history(self, event):
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.history[self.history_index])
        elif self.history_index >= len(self.history) - 1:
            self.history_index = len(self.history)
            self.entry.delete(0, tk.END)
        return "break"

    def run(self):
        self.root.mainloop()