import tkinter as tk
from tkinter import messagebox
from services.config_manager import ConfigManager

class SettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.config_manager = ConfigManager()
        
        # Tiêu đề
        tk.Label(self, text="Cài Đặt Hệ Thống", font=("Arial", 16)).pack(pady=20)
        
        # --- Ô nhập API Key ---
        tk.Label(self, text="Nhập API Key của bạn:").pack(anchor="w", padx=20)
        
        self.entry_key = tk.Entry(self, width=50, show="*") # show="*" để che ký tự
        self.entry_key.pack(padx=20, pady=5)
        
        # Load key cũ lên nếu có
        current_key = self.config_manager.get("api_key")
        self.entry_key.insert(0, current_key)
        
        # --- Nút Lưu ---
        btn_save = tk.Button(self, text="Lưu Cấu Hình", bg="blue", fg="white",
                             command=self.save_settings)
        btn_save.pack(pady=20)

    def save_settings(self):
        new_key = self.entry_key.get().strip()
        
        # Lưu vào file JSON
        self.config_manager.save_config({
            "api_key": new_key
        })
        
        messagebox.showinfo("Thành công", "Đã lưu API Key thành công!")