import os
import subprocess
import requests
import base64
import time
import urllib.parse
import logging
import sys

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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={api_key}"
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["IMAGE"]}}, headers={'Content-Type': 'application/json'})
        if res.status_code != 200:
            logging.error(f"Gemini API Error: {res.text}")
            raise Exception("Gemini Error")
        return base64.b64decode(res.json()['candidates'][0]['content']['parts'][0]['inlineData']['data'])

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
            esc_title = basename.replace("\\", "\\\\").replace(":", "\\:").replace("'", "'\\\\''")
            fc += f"color=c=black@0:s=720x200,format=rgba[txt_canvas];"
            fc += f"[txt_canvas]drawtext=fontfile='{font_path}':text='{esc_title}':fontcolor=white:fontsize=35:borderw=2:bordercolor=black:x=(W-tw)/2:y=(H-th)/2[txt_drawn];"
            fc += f"[txt_drawn]crop=w='max(1, iw * (min(mod(t,20),2)/2))':h=ih:x=0:y=0[txt_wipe];"
            fc += f"{last_stream}[txt_wipe]overlay=0:H-400:enable='lt(mod(t,20),5)',format=yuv420p[v_final]"
        else:
            fc += f"{last_stream}format=yuv420p[v_final]"

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