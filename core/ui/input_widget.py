import tkinter as tk


class FloatingInputWidget:
    def __init__(self, on_submit=None):
        self.on_submit = on_submit

        self.root = tk.Tk()
        self.root.title("Quick Input")

        # Frameless, always on top
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.98)

        self.bg_color = "#F0F2F5"
        self.root.configure(bg=self.bg_color)

        try:
            self.root.wm_attributes("-transparentcolor", self.bg_color)
        except tk.TclError:
            pass

        self.width = 460
        self.height = 58
        self.corner_radius = 100

        # Bottom-right position
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        pos_x = screen_w - self.width - 24
        pos_y = screen_h - self.height - 65

        self.root.geometry(
            f"{self.width}x{self.height}+{pos_x}+{pos_y}"
        )

        self._offset_x = 0
        self._offset_y = 0

        self.history = []
        self.history_index = -1

        self._build_ui()

    def _draw_rounded_rectangle(
        self, canvas, x1, y1, x2, y2, radius=100, **kwargs
    ):
        """Draw a borderless rounded capsule."""
        radius = min(radius, (y2 - y1) / 2, (x2 - x1) / 2)

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

        return canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            **kwargs
        )

    def _build_ui(self):
        # Transparent canvas without any border
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.bg_color,
            highlightthickness=0,
            bd=0,
            relief="flat"
        )
        self.canvas.pack(fill="both", expand=True)

        # Single white capsule: no outer border
        self._draw_rounded_rectangle(
            self.canvas,
            1, 1,
            self.width - 1, self.height - 1,
            radius=self.corner_radius,
            fill="#FFFFFF",
            outline=""
        )

        self.content_frame = tk.Frame(
            self.canvas,
            bg="#FFFFFF",
            bd=0,
            highlightthickness=0
        )

        self.canvas.create_window(
            self.width // 2,
            self.height // 2,
            window=self.content_frame,
            width=self.width - 24,
            height=self.height - 12
        )

        # Drag handle
        self.grip = tk.Label(
            self.content_frame,
            text="⠿",
            font=("Segoe UI", 13),
            fg="#94A3B8",
            bg="#FFFFFF",
            cursor="fleur",
            bd=0
        )
        self.grip.pack(side="left", padx=(5, 5))
        self.grip.bind("<Button-1>", self._start_drag)
        self.grip.bind("<B1-Motion>", self._do_drag)

        # AI icon
        self.icon = tk.Label(
            self.content_frame,
            text="✦",
            font=("Segoe UI", 13, "bold"),
            fg="#10B981",
            bg="#FFFFFF",
            bd=0
        )
        self.icon.pack(side="left", padx=(0, 8))

        # Input field
        self.entry = tk.Entry(
            self.content_frame,
            bg="#FFFFFF",
            fg="#0F172A",
            insertbackground="#10B981",
            selectbackground="#D1FAE5",
            selectforeground="#064E3B",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
            relief="flat"
        )
        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=3,
            padx=(0, 5)
        )

        self.entry.bind("<Return>", lambda event: self._submit())
        self.entry.bind("<Up>", self._prev_history)
        self.entry.bind("<Down>", self._next_history)
        self.entry.focus_set()

        # Submit button
        self.send_btn = tk.Label(
            self.content_frame,
            text="➤",
            font=("Segoe UI", 10, "bold"),
            fg="#059669",
            bg="#ECFDF5",
            padx=8,
            pady=5,
            cursor="hand2",
            bd=0
        )
        self.send_btn.pack(side="right", padx=(3, 4))
        self.send_btn.bind(
            "<Button-1>", lambda event: self._submit()
        )

        # Close button
        self.close_btn = tk.Label(
            self.content_frame,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            fg="#94A3B8",
            bg="#FFFFFF",
            padx=5,
            cursor="hand2",
            bd=0
        )
        self.close_btn.pack(side="right", padx=(0, 3))
        self.close_btn.bind(
            "<Button-1>", lambda event: self.root.destroy()
        )

    def _start_drag(self, event):
        self._offset_x = event.x_root - self.root.winfo_x()
        self._offset_y = event.y_root - self.root.winfo_y()

    def _do_drag(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def _submit(self):
        query = self.entry.get().strip()

        if not query:
            return

        self.history.append(query)
        self.history_index = len(self.history)
        self.entry.delete(0, tk.END)

        if callable(self.on_submit):
            try:
                result = self.on_submit(query)

                # Display callback output in the widget.
                if result is not None:
                    self.show_output(result)

            except Exception as error:
                self.show_output(f"Error: {error}")

    def show_output(self, output):
        """Display output inside the floating widget."""
        self.output_label.configure(text=str(output))
        self.output_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.entry.pack_forget()
        self.send_btn.pack_forget()
        self.icon.pack_forget()

        self.root.update_idletasks()

    def show_input(self):
        """Restore the input interface after displaying output."""
        self.output_label.pack_forget()

        self.icon.pack(side="left", padx=(0, 8))
        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=3,
            padx=(0, 5)
        )
        self.send_btn.pack(side="right", padx=(3, 4))
        self.entry.focus_set()

    def _prev_history(self, event):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(
                0, self.history[self.history_index]
            )

        return "break"

    def _next_history(self, event):
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(
                0, self.history[self.history_index]
            )
        elif self.history_index >= len(self.history) - 1:
            self.history_index = len(self.history)
            self.entry.delete(0, tk.END)

        return "break"

    def run(self):
        # Output display
        self.output_label = tk.Label(
            self.content_frame,
            text="",
            font=("Segoe UI", 10),
            fg="#0F172A",
            bg="#FFFFFF",
            anchor="w",
            bd=0
        )

        self.root.mainloop()


if __name__ == "__main__":
    def process_query(query):
        # Replace this with your AI/ML model execution.
        return f"Processed: {query}"

    widget = FloatingInputWidget(on_submit=process_query)
    widget.run()