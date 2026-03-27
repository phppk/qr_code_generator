import os
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

import qr_code_calc
from draw_qr_code import build_qr_code_v3_l


DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "qr_code.png")
PLACEHOLDER_TEXT = "Paste a YouTube link (or any text) here…"


# Erstellung TKinter GUI.
class QrTkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QR Code Generator (V3-L)")
        self.resizable(False, False)

        self._preview_photo = None
        self._preview_canvas_image_id = None

        root = tk.Frame(self, padx=12, pady=12)
        root.grid(row=0, column=0, sticky="nsew")

        tk.Label(root, text="Text / URL to encode:").grid(row=0, column=0, sticky="w")

        self.entry = tk.Entry(root, width=60)
        self.entry.grid(row=1, column=0, columnspan=3, sticky="we", pady=(4, 8))
        self._placeholder_active = False
        self.entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._set_placeholder()

        tk.Label(root, text="Output file:").grid(row=2, column=0, sticky="w")

        self.out_var = tk.StringVar(value=DEFAULT_OUT)
        self.out_entry = tk.Entry(root, textvariable=self.out_var, width=48)
        self.out_entry.grid(row=3, column=0, columnspan=2, sticky="we", pady=(4, 8))

        tk.Button(root, text="Browse…", command=self.browse_out).grid(
            row=3, column=2, sticky="e", padx=(8, 0), pady=(4, 8)
        )

        tk.Button(root, text="Generate QR", command=self.generate).grid(
            row=4, column=0, sticky="w"
        )

        self.status_var = tk.StringVar(value="")
        tk.Label(root, textvariable=self.status_var).grid(
            row=4, column=1, columnspan=2, sticky="e"
        )

        self.preview_canvas = tk.Canvas(root, width=340, height=340, relief="groove", bd=1, highlightthickness=0)
        self.preview_canvas.grid(row=5, column=0, columnspan=3, pady=(12, 0))
        self.preview_canvas.create_text(170, 170, text="Preview will appear here")

    # Setzten des Placeholder texts in input Field
    def _set_placeholder(self):
        if self.entry.get():
            return
        self.entry.insert(0, PLACEHOLDER_TEXT)
        self.entry.configure(fg="#777777")
        self._placeholder_active = True

    # Leeren des Placeholders wenn Input Field angeklickt wird.
    def _clear_placeholder(self):
        if not self._placeholder_active:
            return
        self.entry.delete(0, tk.END)
        self.entry.configure(fg="black")
        self._placeholder_active = False

    def _on_entry_focus_in(self, _event):
        self._clear_placeholder()

    def _on_entry_focus_out(self, _event):
        if not self.entry.get().strip():
            self.entry.delete(0, tk.END)
            self._set_placeholder()

    def _get_message(self):
        if self._placeholder_active:
            return ""
        return self.entry.get().strip()

    # Datei Picker für Speicherort.
    def browse_out(self):
        path = filedialog.asksaveasfilename(
            title="Save QR Code As",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            initialfile=os.path.basename(self.out_var.get()) or "qr_code.png",
            initialdir=os.path.dirname(self.out_var.get()) or os.path.dirname(DEFAULT_OUT),
        )
        if path:
            self.out_var.set(path)

    def generate(self):
        message = self._get_message()
        if not message:
            messagebox.showerror("Missing input", "Please enter a text/URL to encode.")
            return

        out_path = self.out_var.get().strip() or DEFAULT_OUT
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        except Exception:
            pass

        try:
            # The existing encoder currently reads qr_code_calc.input.
            qr_code_calc.input = message
            build_qr_code_v3_l(output_path=out_path)
        except Exception as e:
            self.status_var.set("Failed")
            messagebox.showerror("Generation failed", str(e))
            return

        try:
            img = Image.open(out_path)
            img = img.convert("RGB").resize((340, 340), Image.NEAREST)
            self._preview_photo = ImageTk.PhotoImage(img)

            self.preview_canvas.delete("all")
            self._preview_canvas_image_id = self.preview_canvas.create_image(
                170, 170, image=self._preview_photo
            )
            self.status_var.set("Saved")
        except Exception as e:
            self.status_var.set("Saved (no preview)")
            messagebox.showwarning("Saved, but preview failed", str(e))


if __name__ == "__main__":
    app = QrTkApp()
    app.mainloop()

