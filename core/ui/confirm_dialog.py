import tkinter as tk


def ask_confirmation(prompt: str, expected_response: str = "yes", parent=None) -> bool:
    """
    Shows a modal confirmation box on top of the screen.
    Returns True only if the user inputs the expected confirmation string.
    """
    result = {"confirmed": False}

    dialog = tk.Toplevel(parent) if parent else tk.Tk()
    dialog.title("Security Confirmation")
    dialog.overrideredirect(True)
    dialog.attributes("-topmost", True)
    dialog.attributes("-alpha", 0.98)
    dialog.configure(bg="#FEF2F2")  # Light red warning background

    width = 420
    height = 170
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    pos_x = (screen_w - width) // 2
    pos_y = (screen_h - height) // 2
    dialog.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    card = tk.Frame(dialog, bg="#FFFFFF", highlightthickness=2, highlightbackground="#EF4444")
    card.pack(fill="both", expand=True, padx=2, pady=2)

    # Header
    header = tk.Frame(card, bg="#FEF2F2", height=30)
    header.pack(fill="x")
    tk.Label(
        header, text="⚠️ DANGEROUS ACTION DETECTED", font=("Segoe UI", 9, "bold"),
        fg="#B91C1C", bg="#FEF2F2"
    ).pack(side="left", padx=10, pady=4)

    # Prompt message
    tk.Label(
        card, text=prompt, font=("Segoe UI", 9), fg="#1F2937",
        bg="#FFFFFF", wraplength=380, justify="left"
    ).pack(padx=12, pady=(10, 6))

    # Entry for confirmation phrase
    entry = tk.Entry(card, bg="#F9FAFB", fg="#111827", font=("Segoe UI", 10), bd=1, relief="solid")
    entry.pack(fill="x", padx=14, ipady=4)
    entry.focus_set()

    # Button Bar
    btn_frame = tk.Frame(card, bg="#FFFFFF")
    btn_frame.pack(fill="x", side="bottom", padx=14, pady=10)

    def on_confirm():
        val = entry.get().strip()
        if val.lower() == expected_response.lower():
            result["confirmed"] = True
            dialog.destroy()
        else:
            entry.delete(0, tk.END)
            entry.config(highlightbackground="#EF4444")

    def on_cancel():
        dialog.destroy()

    tk.Button(
        btn_frame, text="Cancel", font=("Segoe UI", 9), bg="#F3F4F6", fg="#374151",
        bd=0, padx=12, pady=4, cursor="hand2", command=on_cancel
    ).pack(side="right", padx=(6, 0))

    tk.Button(
        btn_frame, text=f"Confirm ('{expected_response}')", font=("Segoe UI", 9, "bold"),
        bg="#EF4444", fg="#FFFFFF", bd=0, padx=12, pady=4, cursor="hand2", command=on_confirm
    ).pack(side="right")

    entry.bind("<Return>", lambda e: on_confirm())
    entry.bind("<Escape>", lambda e: on_cancel())

    # Wait for the modal window to close
    dialog.wait_window()
    return result["confirmed"]