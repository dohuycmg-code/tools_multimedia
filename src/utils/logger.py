import logging
import os
import sys
import tkinter as tk
from logging.handlers import RotatingFileHandler

# --- CẤU HÌNH CỦA BẠN ---
LOG_FILENAME = "app.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3             # Giữ 3 file cũ

def setup_logging():
    """
    Thiết lập hệ thống ghi log (File + Console + Crash Handler)
    """
    # 1. Xác định đường dẫn
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        # src/utils/logger.py -> src/utils -> src -> ROOT
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    log_dir = os.path.join(base_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, LOG_FILENAME)

    # 2. Cấu hình Logger gốc
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Xóa handler cũ để tránh duplicate khi reload
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # --- Handler 1: File ---
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # --- Handler 2: Console ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 3. Bắt lỗi Crash
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("🔥 LỖI NGHIÊM TRỌNG (CRASH):", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

# --- PHẦN BỔ SUNG ĐỂ HIỆN LOG LÊN TOOL ---
class TkinterTextHandler(logging.Handler):
    """Đẩy log lên widget ScrolledText của Tkinter"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            if self.text_widget:
                try:
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state='disabled')
                except:
                    pass
        try:
            self.text_widget.after(0, append)
        except:
            pass

def add_ui_handler(text_widget):
    """Hàm gọi từ UI để gắn log vào textbox"""
    logger = logging.getLogger()
    ui_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
    handler = TkinterTextHandler(text_widget)
    handler.setFormatter(ui_formatter)
    logger.addHandler(handler)