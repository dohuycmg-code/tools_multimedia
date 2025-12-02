import os
import subprocess
import requests
import base64
import time
import urllib.parse
import logging
import sys
from google import genai
import google.generativeai as genai
from google.genai import types
from io import BytesIO

# Dùng logging chuẩn
logger = logging.getLogger(__name__)

class ServiceManager:
    @staticmethod
    def get_app_path():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @staticmethod
    def gen_gemini(api_key, prompt):
        try:
            # Khởi tạo Client với API Key
            client = genai.Client(api_key=api_key)
            if not prompt:
                    # Fallback nếu người dùng xóa hết text
                    prompt = "Create a highly detailed, photorealistic, vertical (9:16) image prompt in English describing a musical artist whose appearance and atmospheric surroundings visually metaphorize the mood of the song title: '{title}'. "
                
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt_query = prompt.replace("{title}")
            res = model.generate_content(prompt_query)
            prompt = res.text.strip()
            
            # Gọi model tạo ảnh
            response = client.models.generate_images(
                model='imagen-4.0-fast-generate-001', 
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1, # Chỉ lấy 1 ảnh để giống logic cũ
                    aspect_ratio="1:1"  # Tùy chỉnh tỉ lệ nếu cần
                )
            )

            # Kiểm tra và xử lý kết quả
            if response.generated_images:
                # Lấy ảnh đầu tiên (dạng PIL.Image)
                pil_image = response.generated_images[0].image
                
                # Chuyển đổi PIL Image thành bytes để tương thích với code ghi file cũ của bạn
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                return img_byte_arr.getvalue()
            else:
                raise Exception("No image returned from API")

        except Exception as e:
            logging.error(f"GenAI SDK Error: {e}")
            raise

    @staticmethod
    def render_video(img_path, audio_path, out_path, active_effects, font_path):
        app_path = ServiceManager.get_app_path()
        ffmpeg_exe = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
        ffmpeg_cmd = os.path.join(app_path, ffmpeg_exe)
        if not os.path.exists(ffmpeg_cmd): 
            ffmpeg_cmd = "ffmpeg"

        filename = os.path.basename(audio_path)
        basename = os.path.splitext(filename)[0]

        inputs = ['-loop', '1', '-i', img_path, '-i', audio_path]
        for eff in active_effects:
            inputs.extend(['-stream_loop', '-1', '-i', eff['path']])

        # Filter Complex logic (Giữ nguyên logic gốc)
        fc = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,format=gbrp[bg];"
        last_stream = "[bg]"
        eff_idx = 2
        
        for eff in active_effects:
            # Logic xử lý effect
            ext = os.path.splitext(eff['path'])[1].lower()
            is_video = ext in ['.mp4', '.mov', '.avi']
            
            fc += f"[{eff_idx}:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,format=gbrp[eff_{eff_idx}];"
            enable_expr = f"gte(t,{eff['start']})"
            if eff['end'] > 0: enable_expr += f"*lte(t,{eff['end']})"
            
            if is_video:
                fc += f"{last_stream}[eff_{eff_idx}]blend=all_mode='screen':enable='{enable_expr}',format=gbrp[v_tmp_{eff_idx}];"
            else:
                fc += f"{last_stream}[eff_{eff_idx}]overlay=0:0:enable='{enable_expr}',format=gbrp[v_tmp_{eff_idx}];"
            last_stream = f"[v_tmp_{eff_idx}]"
            eff_idx += 1

        # Logic Text
        if font_path and os.path.exists(font_path):
            # 1. Xử lý đường dẫn Font cho chuẩn FFmpeg (Quan trọng trên Windows)
            # Thay \ thành / và escape dấu : (Ví dụ C: -> C\:)
            safe_font_path = font_path.replace("\\", "/").replace(":", "\\:")
            
            # 2. Xử lý tên bài hát (Bỏ dấu ' để tránh lỗi lệnh)
            esc_title = basename.replace(":", "\\:").replace("'", "")
            
            # 3. Vẽ chữ (Bỏ enable để đảm bảo chạy ổn định 100%)
            # Tạo luồng [v_txt] riêng biệt
            fc += f"color=c=black@0:s=720x200,format=rgba[txt_canvas];"
            fc += (
                f"[txt_canvas]drawtext=fontfile='{safe_font_path}':text='{esc_title}':"
                "fontcolor=white:fontsize=35:borderw=2:bordercolor=black:"
                "x=(W-tw)/2:y=(H-th)/2[txt_drawn];"
            )
            fc += (
                f"[txt_drawn]crop=w='max(1, iw * (min(mod(t,20),2)/2))':h=ih:x=0:y=0[txt_wipe];"
            )
            fc += f"{last_stream}[txt_wipe]overlay=0:H-400:enable='lt(mod(t,20),5)',format=yuv420p[v_final]"
            last_stream = "[v_final]"
        else:
            fc += f"{last_stream}format=yuv420p[v_final]"
            last_stream = "[v_final]"

        cmd = [
            ffmpeg_cmd, '-y', *inputs, '-filter_complex', fc,
            '-map', '[v_final]', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p', '-shortest',
            out_path
        ]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)