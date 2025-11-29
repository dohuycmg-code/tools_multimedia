import logging
import os
import time
import google.generativeai as genai
from services.config_manager import ConfigManager

class AudiosToSubtitlesEngine:
    def __init__(self, model_name):
        self.config_manager = ConfigManager()
        self.api_key = self.config_manager.get("api_key")
        self.model_name = model_name
        self.setup_api()

    def setup_api(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logging.error(f"Lỗi cấu hình API Gemini: {e}")

    def process_folder(self, folder_path, log_callback, status_callback):
        """
        folder_path: Đường dẫn thư mục
        log_callback: Hàm để gửi text log về UI
        status_callback: Hàm để gửi trạng thái ngắn về UI
        """
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.mp3', '.wav'))]
        total = len(files)

        if total == 0:
            log_callback("⚠️ Không tìm thấy file video/audio nào!")
            return

        for idx, file_name in enumerate(files):
            status_callback(f"Đang xử lý ({idx+1}/{total}): {file_name}")
            file_path = os.path.join(folder_path, file_name)
            base_name = os.path.splitext(file_path)[0]
            srt_path = f"{base_name}.srt"
            
            log_callback(f"\n🎥 Đang xử lý: {file_name}")
            
            uploaded_file = None
            try:
                log_callback("   ☁️  Đang upload file lên Google Cloud...")
                uploaded_file = genai.upload_file(file_path)
                
                log_callback("   ⏳ Đang chờ Google xử lý file...")
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = genai.get_file(uploaded_file.name)
                
                if uploaded_file.state.name == "FAILED":
                    log_callback("   ❌ Upload thất bại.")
                    continue

                log_callback("   🧠 Đang yêu cầu Gemini tạo phụ đề (SRT)...")
                prompt = (
                    "Hãy đóng vai chuyên gia phụ đề. Tạo file SRT chuẩn tiếng Việt cho video này. "
                    "Yêu cầu: Thời gian chính xác, không markdown, không lời dẫn thừa."
                )

                response = self.model.generate_content([uploaded_file, prompt])
                srt_content = response.text
                
                # Clean markdown
                if srt_content.startswith("```"):
                    lines = srt_content.splitlines()
                    if lines and lines[0].startswith("```"): lines = lines[1:]
                    if lines and lines[-1].startswith("```"): lines = lines[:-1]
                    srt_content = "\n".join(lines)
                
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(srt_content.strip())
                
                log_callback(f"   ✅ Đã tạo xong: {os.path.basename(srt_path)}")

            except Exception as e:
                log_callback(f"   ❌ Lỗi: {e}")
            
            finally:
                if uploaded_file:
                    try:
                        genai.delete_file(uploaded_file.name)
                    except: pass
        
        status_callback("Hoàn tất!")
        log_callback("\n--- HOÀN TẤT ---")