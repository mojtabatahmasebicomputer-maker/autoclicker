import time
import random
import datetime
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui

try:
    import keyboard
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

# ============ کلیدهای میانبر (قابل تغییر) ============
TOGGLE_HOTKEY = "f8"   # شروع / توقف
EXIT_HOTKEY = "f9"     # خروج از برنامه
# =====================================================


def parse_hms(text):
    text = text.strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.datetime.strptime(text, fmt).time()
            return datetime.datetime.combine(datetime.date.today(), t)
        except ValueError:
            pass
    raise ValueError(f"فرمت زمان اشتباه است: {text}")


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.stop_event = threading.Event()
        self.worker = None
        self.counter = 0
        self.running = False

        self.toggle_key_var = tk.StringVar(value=TOGGLE_HOTKEY)
        self.exit_key_var = tk.StringVar(value=EXIT_HOTKEY)
        self.start_var = tk.StringVar(value="08:00:00")
        self.use_start_time_var = tk.BooleanVar(value=False)
        self.use_end_var = tk.BooleanVar(value=True)
        self.end_var = tk.StringVar(value="12:00:00")
        self.use_pos_var = tk.BooleanVar(value=True)
        self.x_var = tk.StringVar(value="500")
        self.y_var = tk.StringVar(value="400")
        self.count_var = tk.StringVar(value="0")
        self.min_var = tk.StringVar(value="0.290")
        self.max_var = tk.StringVar(value="0.310")
        self.button_var = tk.StringVar(value="left")
        self.status_var = tk.StringVar(value="آماده")
        self.counter_var = tk.StringVar(value="تعداد کلیک: 0")

        self.build_ui()
        self.register_hotkeys()

    # ---------- رابط ----------
    def build_ui(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.grid(sticky="nsew")

        hk_box = ttk.LabelFrame(frm, text="کلیدهای میانبر", padding=8)
        hk_box.grid(row=0, column=0, sticky="ew", pady=4)
        ttk.Label(hk_box, text="شروع / توقف:").grid(row=0, column=0, sticky="w")
        ttk.Entry(hk_box, textvariable=self.toggle_key_var, width=8, justify="center").grid(row=0, column=1, padx=6)
        ttk.Label(hk_box, text="خروج:").grid(row=0, column=2, sticky="w")
        ttk.Entry(hk_box, textvariable=self.exit_key_var, width=8, justify="center").grid(row=0, column=3, padx=6)
        ttk.Button(hk_box, text="اعمال کلیدها", command=self.register_hotkeys).grid(row=1, column=0, columnspan=4, pady=(6, 0), sticky="ew")

        time_box = ttk.LabelFrame(frm, text="زمان", padding=8)
        time_box.grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Checkbutton(time_box, text="شروع در ساعت مشخص:", variable=self.use_start_time_var,
                        command=self.toggle_fields).grid(row=0, column=0, sticky="w")
        self.start_entry = ttk.Entry(time_box, textvariable=self.start_var, width=14, justify="center")
        self.start_entry.grid(row=0, column=1, padx=6)
        ttk.Checkbutton(time_box, text="خروج خودکار در ساعت:", variable=self.use_end_var,
                        command=self.toggle_fields).grid(row=1, column=0, sticky="w", pady=4)
        self.end_entry = ttk.Entry(time_box, textvariable=self.end_var, width=14, justify="center")
        self.end_entry.grid(row=1, column=1, padx=6)

        pos_box = ttk.LabelFrame(frm, text="محل کلیک", padding=8)
        pos_box.grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Checkbutton(pos_box, text="به مختصات زیر برو و کلیک کن",
                        variable=self.use_pos_var).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(pos_box, text="X:").grid(row=1, column=0, sticky="e")
        ttk.Entry(pos_box, textvariable=self.x_var, width=8).grid(row=1, column=1, padx=4)
        ttk.Label(pos_box, text="Y:").grid(row=1, column=2, sticky="e")
        ttk.Entry(pos_box, textvariable=self.y_var, width=8).grid(row=1, column=3, padx=4)
        ttk.Button(pos_box, text="انتخاب مختصات (۳ ثانیه بعد)",
                   command=self.capture_position).grid(row=2, column=0, columnspan=4, pady=6, sticky="ew")

        click_box = ttk.LabelFrame(frm, text="تنظیمات کلیک", padding=8)
        click_box.grid(row=3, column=0, sticky="ew", pady=4)
        ttk.Label(click_box, text="تعداد کلیک (0 = بی‌نهایت):").grid(row=0, column=0, sticky="w")
        ttk.Entry(click_box, textvariable=self.count_var, width=10, justify="center").grid(row=0, column=1, padx=6)
        ttk.Label(click_box, text="کمترین فاصله (ثانیه):").grid(row=1, column=0, sticky="w")
        ttk.Entry(click_box, textvariable=self.min_var, width=10, justify="center").grid(row=1, column=1, padx=6)
        ttk.Label(click_box, text="بیشترین فاصله (ثانیه):").grid(row=2, column=0, sticky="w")
        ttk.Entry(click_box, textvariable=self.max_var, width=10, justify="center").grid(row=2, column=1, padx=6)
        ttk.Label(click_box, text="دکمه موس:").grid(row=3, column=0, sticky="w")
        ttk.Combobox(click_box, textvariable=self.button_var, values=["left", "right"],
                     state="readonly", width=8).grid(row=3, column=1, padx=6, sticky="w")

        ctrl = ttk.Frame(frm)
        ctrl.grid(row=4, column=0, sticky="ew", pady=8)
        self.toggle_btn = ttk.Button(ctrl, text="شروع", command=self.toggle)
        self.toggle_btn.grid(row=0, column=0, padx=4, sticky="ew")
        ttk.Button(ctrl, text="خروج", command=self.exit_app).grid(row=0, column=1, padx=4, sticky="ew")
        ctrl.columnconfigure((0, 1), weight=1)

        ttk.Label(frm, textvariable=self.counter_var, font=("Arial", 11, "bold")).grid(row=5, column=0)
        ttk.Label(frm, textvariable=self.status_var, foreground="gray").grid(row=6, column=0, sticky="w")
        hint = "میانبرها از هر جایی در ویندوز کار می‌کنن، حتی وقتی پنجره برنامه فعال نیست."
        if not HAS_KEYBOARD:
            hint += "\n(کتابخانه keyboard نصب نیست؛ میانبر غیرفعال است)"
        ttk.Label(frm, text=hint, foreground="gray").grid(row=7, column=0, sticky="w", pady=(6, 0))

        self.toggle_fields()

    def toggle_fields(self):
        self.start_entry.configure(state="normal" if self.use_start_time_var.get() else "disabled")
        self.end_entry.configure(state="normal" if self.use_end_var.get() else "disabled")

    # ---------- میانبرها ----------
    def register_hotkeys(self):
        if not HAS_KEYBOARD:
            return
        try:
            keyboard.unhook_all_hotkeys()
            keyboard.add_hotkey(self.toggle_key_var.get().strip(), lambda: self.root.after(0, self.toggle))
            keyboard.add_hotkey(self.exit_key_var.get().strip(), lambda: self.root.after(0, self.exit_app))
            self.status_var.set("میانبرها اعمال شد.")
        except Exception as e:
            messagebox.showerror("خطا", f"کلید میانبر نامعتبر است: {e}")

    # ---------- مختصات ----------
    def capture_position(self):
        self.status_var.set("۳ ثانیه تا ثبت مختصات... موس را روی نقطه مورد نظر ببرید")
        self.root.after(3000, self._do_capture)

    def _do_capture(self):
        x, y = pyautogui.position()
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        self.use_pos_var.set(True)
        self.status_var.set(f"مختصات ثبت شد: X={x} Y={y}")

    # ---------- شروع / توقف (یک دکمه) ----------
    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        try:
            cfg = self.read_config()
        except ValueError as e:
            messagebox.showerror("خطا", str(e))
            return

        self.stop_event.clear()
        self.counter = 0
        self.counter_var.set("تعداد کلیک: 0")
        self.running = True
        self.toggle_btn.configure(text="توقف")
        self.worker = threading.Thread(target=self.run_clicks, args=(cfg,), daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_event.set()
        self.status_var.set("در حال توقف...")

    def exit_app(self):
        self.stop_event.set()
        self.root.after(100, self.root.destroy)

    def finish(self, message):
        self.running = False
        self.toggle_btn.configure(text="شروع")
        self.status_var.set(message)

    # ---------- تنظیمات ----------
    def read_config(self):
        cfg = {"start": None, "end": None, "pos": None}
        now = datetime.datetime.now()

        if self.use_start_time_var.get():
            start = parse_hms(self.start_var.get())
            if start <= now:
                start += datetime.timedelta(days=1)
            cfg["start"] = start

        if self.use_end_var.get():
            end = parse_hms(self.end_var.get())
            ref = cfg["start"] or now
            if end <= ref:
                end += datetime.timedelta(days=1)
            cfg["end"] = end

        if self.use_pos_var.get():
            cfg["pos"] = (int(self.x_var.get()), int(self.y_var.get()))

        cfg["count"] = int(self.count_var.get())
        cfg["min"] = float(self.min_var.get())
        cfg["max"] = float(self.max_var.get())
        if cfg["min"] < 0 or cfg["max"] < cfg["min"]:
            raise ValueError("فاصله بین کلیک‌ها معتبر نیست.")
        if cfg["count"] < 0:
            raise ValueError("تعداد کلیک نمی‌تواند منفی باشد.")
        cfg["button"] = self.button_var.get()
        return cfg

    # ---------- حلقه کلیک ----------
    def run_clicks(self, cfg):
        try:
            if cfg["start"]:
                self.set_status(f"در انتظار {cfg['start'].strftime('%Y-%m-%d %H:%M:%S')}")
                while datetime.datetime.now() < cfg["start"]:
                    if self.stop_event.is_set():
                        return self.done("متوقف شد قبل از شروع.")
                    time.sleep(0.2)

            if cfg["pos"]:
                pyautogui.moveTo(cfg["pos"][0], cfg["pos"][1], duration=0.3)

            self.set_status("در حال کلیک...")
            while not self.stop_event.is_set():
                if cfg["end"] and datetime.datetime.now() >= cfg["end"]:
                    return self.done("به ساعت خروج رسید.")
                if cfg["count"] and self.counter >= cfg["count"]:
                    return self.done("به تعداد تعیین‌شده رسید.")

                if cfg["pos"]:
                    pyautogui.click(cfg["pos"][0], cfg["pos"][1], button=cfg["button"])
                else:
                    pyautogui.click(button=cfg["button"])

                self.counter += 1
                self.root.after(0, self.counter_var.set, f"تعداد کلیک: {self.counter}")
                time.sleep(random.uniform(cfg["min"], cfg["max"]))

            self.done("متوقف شد.")
        except pyautogui.FailSafeException:
            self.done("متوقف شد (موس به گوشه رفت).")
        except Exception as e:
            self.done(f"خطا: {e}")

    def set_status(self, text):
        self.root.after(0, self.status_var.set, text)

    def done(self, message):
        self.root.after(0, self.finish, f"{message} | کل کلیک‌ها: {self.counter}")


if __name__ == "__main__":
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()
