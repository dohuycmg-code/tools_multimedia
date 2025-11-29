import customtkinter as ctk
from tkinter import filedialog
import json
import os
from services.audio_engine import AudiosToSubtitlesEngine

class SubtitlesPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Load Config
        self.load_config()

        # Layout
        self.grid_columnconfigure(0, weight=1)

        # 1. Chọn Folder
        self.label_info = ctk.CTkLabel(self, text="Chọn thư mục chứa video", font=("Arial", 16))
        self.label_info.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))

        self.entry_path = ctk.CTkEntry(self, placeholder_text="Đường dẫn thư mục...")
        self.entry_path.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="ew")

        self.btn_browse = ctk.CTkButton(self, text="Chọn Folder...", width=100, command=self.browse_folder_event)
        self.btn_browse.grid(row=1, column=1, padx=(0, 20), pady=10)

        # 2. Nút Submit
        self.btn_submit = ctk.CTkButton(self, text="Bắt đầu tạo Subtitles", 
                                        height=40, font=("Arial", 14, "bold"), 
                                        command=self.submit_event)
        self.btn_submit.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        # 3. Log
        self.textbox_log = ctk.CTkTextbox(self, height=300)
        self.textbox_log.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="nsew")
        self.textbox_log.insert("0.0", "Sẵn sàng...\n")

        # 4. Status Label (ẩn/hiện tuỳ ý, ở đây mình dùng chung log hoặc thêm label dưới)
        self.status_label = ctk.CTkLabel(self, text="Trạng thái: Chờ lệnh", anchor="w")
        self.status_label.grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="w")

    def load_config(self):
        # Đọc file json từ thư mục config
        try:
            config_path = os.path.join("settings.json")
            with open(config_path, "r") as f:
                config = json.load(f)
                self.api_key = config.get("api_key")
                self.model_name = config.get("model_name")
        except Exception:
            self.api_key = ""
            self.model_name = "gemini-2.5-flash"

    def browse_folder_event(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, folder)

    def log_message(self, message):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")
        self.update() # Cập nhật UI ngay lập tức

    def update_status(self, message):
        self.status_label.configure(text=f"Trạng thái: {message}")
        self.update()

    def submit_event(self):
        path = self.entry_path.get()
        if not path:
            self.log_message("❌ Vui lòng chọn thư mục!")
            return
        
        # Khởi tạo Engine và chạy
        engine = AudiosToSubtitlesEngine("gemini-2.5-flash")
        engine.process_folder(path, self.log_message, self.update_status)