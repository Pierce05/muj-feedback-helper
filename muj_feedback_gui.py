"""
Simple window for the MUJ feedback helper.
Keep this file in the same folder as muj_feedback.py and run:  python muj_feedback_gui.py
Your password is only held in memory while the run is in progress.
"""
import contextlib
import queue
import threading
import tkinter as tk
from tkinter import ttk

import muj_feedback

DONE = object()


class QueueWriter:
    """Sends everything the engine prints into the window's log box."""

    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(text)

    def flush(self):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MUJ Feedback Helper")
        self.geometry("620x640")
        self.minsize(520, 560)
        self.q = queue.Queue()
        self.running = False

        pad = {"padx": 16, "pady": 6}
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="MUJ Feedback Helper", font=("Segoe UI", 16, "bold")).pack(anchor="w", **pad)
        ttk.Label(
            main,
            text="Fills and submits every pending faculty feedback form.\n"
                 "Runs only on your computer. Nothing is saved.",
            foreground="#555",
        ).pack(anchor="w", padx=16)

        # Feedback type
        box = ttk.LabelFrame(main, text="Feedback type")
        box.pack(fill="x", **pad)
        self.mode = tk.StringVar(value="p")
        for text, val in (("Positive (YES / best rating)", "p"),
                          ("Mid / balanced (mixed YES-NO / middle rating)", "m"),
                          ("Negative (NO / lowest rating)", "n")):
            ttk.Radiobutton(box, text=text, value=val, variable=self.mode).pack(anchor="w", padx=10, pady=2)

        # Login
        login = ttk.LabelFrame(main, text="Portal login")
        login.pack(fill="x", **pad)
        row = ttk.Frame(login)
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text="Username", width=10).pack(side="left")
        self.user = ttk.Entry(row)
        self.user.pack(side="left", fill="x", expand=True)
        ttk.Label(row, text="@muj.manipal.edu", foreground="#555").pack(side="left", padx=4)

        row = ttk.Frame(login)
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text="Password", width=10).pack(side="left")
        self.pw = ttk.Entry(row, show="•")
        self.pw.pack(side="left", fill="x", expand=True)
        self.show = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Show", variable=self.show,
                        command=lambda: self.pw.config(show="" if self.show.get() else "•")).pack(side="left", padx=4)

        # Options and start
        self.dry = tk.BooleanVar(value=False)
        ttk.Checkbutton(main, text="Preview only (dry run: nothing is clicked or submitted)",
                        variable=self.dry).pack(anchor="w", **pad)
        self.btn = ttk.Button(main, text="Fill and submit all pending forms", command=self.start)
        self.btn.pack(fill="x", padx=16, pady=6, ipady=6)

        # Log
        ttk.Label(main, text="Progress").pack(anchor="w", padx=16)
        frame = ttk.Frame(main)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.log = tk.Text(frame, height=12, wrap="word", state="disabled", font=("Consolas", 9))
        sb = ttk.Scrollbar(frame, command=self.log.yview)
        self.log.config(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.after(100, self.poll)

    def write(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")

    def poll(self):
        try:
            while True:
                item = self.q.get_nowait()
                if item is DONE:
                    self.running = False
                    self.btn.config(state="normal", text="Fill and submit all pending forms")
                else:
                    self.write(item)
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def start(self):
        if self.running:
            return
        username = self.user.get().strip().split("@")[0]
        password = self.pw.get()
        if not username or not password:
            self.write("Enter your username and password first.\n")
            return
        mode, dry = self.mode.get(), self.dry.get()
        self.pw.delete(0, "end")  # don't keep the password in the window
        self.running = True
        self.btn.config(state="disabled", text="Running... a browser window will open")
        self.write(f"\n--- Started ({'preview' if dry else 'live'}, mode {mode}) ---\n")
        threading.Thread(target=self.worker, args=(mode, username, password, dry), daemon=True).start()

    def worker(self, mode, username, password, dry):
        try:
            with contextlib.redirect_stdout(QueueWriter(self.q)):
                muj_feedback.run(mode, username, password, dry)
        except SystemExit as e:
            self.q.put(f"\n{e}\n")
        except Exception as e:
            self.q.put(f"\nError: {e}\n")
        finally:
            self.q.put("\nFinished. You can close this window.\n")
            self.q.put(DONE)


if __name__ == "__main__":
    App().mainloop()
