import json
import logging
import os
import sys

CONFIG_FILE = "settings.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "save_folder": "C:/Downloads",
    "theme": "light"
}

class ConfigManager:
    def __init__(self):
        """
        Quản lý việc đọc, ghi và cập nhật file cấu hình settings.json.
        """
        self.config_path = self._get_config_path()
        self.config = self.load_config()
        logging.info(f"File cấu hình được quản lý tại: {self.config_path}")

    def _get_config_path(self):
        """
        Xác định đường dẫn chính xác đến file config, dù chạy dưới dạng script Python
        hay file .exe đã được đóng gói.
        """
        # Nếu đang chạy bằng file .exe (đã đóng gói bởi PyInstaller)
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        # Nếu đang chạy bằng file .py thông thường
        else:
            # Lấy đường dẫn của thư mục gốc dự án (chứa file main.py)
            # Điều này giúp đường dẫn luôn đúng dù file này được gọi từ đâu
            try:
                # __main__ chỉ tồn tại khi chạy trực tiếp file
                import __main__ as main
                base_path = os.path.dirname(os.path.abspath(main.__file__))
            except (ImportError, AttributeError):
                 # Fallback: Nếu không tìm thấy main, giả sử cấu trúc dự án chuẩn
                base_path = os.path.abspath(".")

        config_path = os.path.join(base_path, CONFIG_FILE)
        return config_path

    def load_config(self):
        """
        Tải cấu hình từ file JSON. Nếu file không tồn tại hoặc bị lỗi,
        sẽ tạo file mới với cấu hình mặc định.
        """
        if not os.path.exists(self.config_path):
            logging.warning(f"Không tìm thấy file cấu hình tại '{self.config_path}'. Đang tạo file mới với cấu hình mặc định.")
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                logging.info("Tải cấu hình thành công.")
                return config_data
        except json.JSONDecodeError:
            logging.error(f"Lỗi giải mã JSON trong file '{self.config_path}'. Dữ liệu có thể bị hỏng. Đang sử dụng cấu hình mặc định.")
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"Lỗi không xác định khi tải file cấu hình: {e}. Đang sử dụng cấu hình mặc định.")
            return DEFAULT_CONFIG.copy()

    def save_config(self, new_data):
        """
        Lưu hoặc cập nhật dữ liệu cấu hình vào file JSON.
        """
        # Cập nhật từ điển config hiện tại của instance với dữ liệu mới
        # self.config.update(new_data) # Gây ra bug lặp, vì new_data đã là self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
            
            # Sau khi ghi thành công, cập nhật lại config của class
            self.config = new_data.copy()
            logging.info(f"Đã lưu cấu hình thành công vào '{self.config_path}'.")

        except Exception as e:
            logging.error(f"Lỗi khi lưu cấu hình: {e}")


    def get(self, key, default=None):
        """
        Lấy một giá trị từ cấu hình theo 'key'.
        Trả về giá trị mặc định nếu không tìm thấy.
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """
        Đặt một giá trị mới cho một 'key' và lưu lại cấu hình.
        """
        self.config[key] = value
        self.save_config(self.config)
        logging.info(f"Đã cập nhật cấu hình: '{key}' = '{value}'")