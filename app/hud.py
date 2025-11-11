
import os
import tkinter as tk
from queue import Empty

class TkHud:
    COLORS = {
        "dt": "#a0a0a0",
        "scope": "#7adfff",
        "name": "#ffb86c",
        "msg": "#ffffff",
        "meta": "#8f8f8f",
        "err": "#ff6b6b",
    }

    def __init__(self, queue, alpha: float = 0.75, font="Consolas 11"):
        self.queue = queue
        self.root = tk.Tk()
        self.root.title("CS2 Chat HUD")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        self.root.wm_attributes("-alpha", alpha)
        self.visible = True

        if os.name == "nt":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        w, h = 800, 320
        self.root.geometry(f"{w}x{h}+40+720")

        self._drag = {"x": 0, "y": 0}
        self.root.bind("<Button-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._on_move)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<F1>", self._toggle_visible)
        self.root.bind("<F2>", lambda e: self._cycle_alpha())

        frame = tk.Frame(self.root, bg="black")
        frame.pack(fill="both", expand=True)

        # Topbar mit Close-Button ✕
        topbar = tk.Frame(frame, bg="black")
        topbar.pack(fill="x", side="top")

        close_btn = tk.Label(topbar, text="✕", fg="#ff6666", bg="black",
                             font=("Consolas", 14, "bold"), cursor="hand2")
        close_btn.pack(side="right", padx=6, pady=2)
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#ffaaaa"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#ff6666"))
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())

        self.text = tk.Text(
            frame,
            bg="black", fg=self.COLORS["meta"],
            insertbackground="white",
            relief="flat", bd=0, highlightthickness=0,
            wrap="word"
        )
        self.text.pack(fill="both", expand=True, padx=8, pady=4)
        self.text.configure(font=font, state="disabled")

        for tag, color in self.COLORS.items():
            self.text.tag_configure(tag, foreground=color)

        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Button-4>", lambda e: self.text.yview_scroll(-1, "units"))
        self.text.bind("<Button-5>", lambda e: self.text.yview_scroll(1, "units"))

        self._poll()

    def _cycle_alpha(self):
        cur = float(self.root.attributes("-alpha"))
        next_alpha = 0.9 if cur < 0.8 else 0.6 if cur < 0.9 else 0.75
        self.root.attributes("-alpha", next_alpha)

    def _toggle_visible(self, *_):
        self.visible = not self.visible
        self.root.withdraw() if not self.visible else self.root.deiconify()

    def _start_move(self, event):
        self._drag["x"], self._drag["y"] = event.x, event.y

    def _on_move(self, event):
        x, y = event.x_root - self._drag["x"], event.y_root - self._drag["y"]
        self.root.geometry(f"+{x}+{y}")

    def _on_mousewheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.text.yview_scroll(delta, "units")

    def _trim_if_needed(self):
        lines = int(self.text.index('end-1c').split('.')[0])
        if lines > 2000:
            self.text.delete('1.0', '200.0')

    def _poll(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                if typ == "structured":
                    self._append_struct(**payload)
                elif typ == "line":
                    self._append_line(payload)
                elif typ == "error":
                    self._append_line(payload, tag="err")
                self.queue.task_done()
        except Empty:
            pass
        self.root.after(33, self._poll)

    def _append_line(self, line: str, tag="meta"):
        self.text.configure(state="normal")
        self.text.insert("end", line.rstrip() + "\n", (tag,))
        self._trim_if_needed()
        self.text.see("end")
        self.text.configure(state="disabled")

    def _append_struct(self, dt: str, scope: str, name: str, msg: str):
        self.text.configure(state="normal")
        self.text.insert("end", dt + "  ", ("dt",))
        self.text.insert("end", f"[{scope}] ", ("scope",))
        self.text.insert("end", name + ": ", ("name",))
        self.text.insert("end", msg + "\n", ("msg",))
        self._trim_if_needed()
        self.text.see("end")
        self.text.configure(state="disabled")

    def run(self):
        self.root.mainloop()
