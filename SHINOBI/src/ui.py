import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging
from config_manager import ConfigManager

logger = logging.getLogger("SHINOBI.UI")

class ShinobiLockScreen:
    """
    SHINOBIの全画面ロック画面 UI。
    """
    def __init__(self, root, on_auth_success=None):
        self.root = root
        self.root.title("SHINOBI - ACCESS DENIED")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.wm_attributes("-topmost", True)
        self.on_auth_success = on_auth_success

        self.create_widgets()

    def create_widgets(self):
        self.title_label = tk.Label(
            self.root, text="SHINOBI", font=("Consolas", 72, "bold"),
            fg="#FF0000", bg="black"
        )
        self.title_label.pack(pady=(100, 20))

        self.status_label = tk.Label(
            self.root, text="SCANNING FOR AUTHORIZED DEVICE...",
            font=("Consolas", 18), fg="#00FF00", bg="black"
        )
        self.status_label.pack(pady=20)

        self.pin_frame = tk.Frame(self.root, bg="black")
        self.pin_frame.pack(pady=40)

        tk.Label(self.pin_frame, text="ENTER PIN:", font=("Consolas", 14), fg="white", bg="black").pack(side=tk.LEFT, padx=10)
        self.pin_entry = tk.Entry(self.pin_frame, show="*", font=("Consolas", 24), width=10, bg="#222", fg="white", insertbackground="white")
        self.pin_entry.pack(side=tk.LEFT)
        self.pin_entry.bind("<Return>", self.on_pin_submit)

        self.unlock_btn = tk.Button(
            self.root, text="UNLOCK", command=self.on_pin_submit,
            font=("Consolas", 18), bg="#333", fg="white", width=15, relief=tk.FLAT
        )
        self.unlock_btn.pack(pady=20)

    def on_pin_submit(self, event=None):
        pin = self.pin_entry.get()
        if ConfigManager.verify_pin(pin):
            self.show_unlock_animation()
            if self.on_auth_success:
                self.on_auth_success("PIN")
        else:
            self.pin_entry.delete(0, tk.END)
            self.status_label.config(text="ACCESS DENIED: INCORRECT PIN", fg="red")
            logger.warning("Incorrect PIN attempt.")

    def show_unlock_animation(self):
        self.status_label.config(text="ACCESS GRANTED. WELCOME MASTER.", fg="#00FF00")
        self.root.after(1000, self.root.destroy)

class AdminDashboard:
    """
    管理者用設定画面 UI。
    """
    def __init__(self, root):
        self.root = root
        self.root.title("SHINOBI ADMIN DASHBOARD")
        self.root.geometry("800x600")
        ConfigManager.initialize()
        self.create_widgets()

    def create_widgets(self):
        tab_control = ttk.Notebook(self.root)

        sensor_tab = ttk.Frame(tab_control)
        tab_control.add(sensor_tab, text="Sensors")
        self.build_sensor_tab(sensor_tab)

        log_tab = ttk.Frame(tab_control)
        tab_control.add(log_tab, text="Audit Logs")
        self.build_log_tab(log_tab)

        tab_control.pack(expand=1, fill="both")

    def build_sensor_tab(self, parent):
        ttk.Label(parent, text="Bluetooth Proximity Threshold (dBm):", font=("Consolas", 12)).pack(pady=(20, 5))
        self.rssi_slider = ttk.Scale(parent, from_=-90, to=-30, orient="horizontal")
        self.rssi_slider.set(ConfigManager.get("rssi_threshold"))
        self.rssi_slider.pack(pady=10, fill="x", padx=40)

        ttk.Label(parent, text="Face Recognition Threshold (Strict 0.3 - 0.7 Loose):", font=("Consolas", 12)).pack(pady=(20, 5))
        self.face_slider = ttk.Scale(parent, from_=0.3, to_=0.7, orient="horizontal")
        self.face_slider.set(ConfigManager.get("face_threshold"))
        self.face_slider.pack(pady=10, fill="x", padx=40)

        ttk.Button(parent, text="Apply Changes", command=self.save_settings).pack(pady=40)

    def build_log_tab(self, parent):
        self.log_list = tk.Listbox(parent, font=("Consolas", 10), bg="#f0f0f0")
        self.log_list.pack(expand=1, fill="both", padx=10, pady=10)

    def save_settings(self):
        ConfigManager.set("rssi_threshold", int(self.rssi_slider.get()))
        ConfigManager.set("face_threshold", round(float(self.face_slider.get()), 2))
        messagebox.showinfo("SHINOBI", "Settings applied successfully.")
        logger.info("Settings updated via Admin Dashboard.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()
