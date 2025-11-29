import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import glob
from threading import Thread
import logging

# Import các service
from src.services.video_engine import ServiceManager
from src.utils.logger import add_ui_handler
from src.services.config_manager import ConfigManager 

class VideoPage(tk.Frame): 
    def __init__(self, parent):
        super().__init__(parent) 
        
        # Lấy API Key từ Config
        self.config_manager = ConfigManager()
        self.api_key = self.config_manager.get("api_key")
        
        self.input_dir = ""
        self.output_dir = ""
        
        # List lưu trữ hiệu ứng: [{'path': '...', 'start': 0, 'end': 10}, ...]
        self.custom_effects = []
        
        self.create_widgets()
        add_ui_handler(self.log_area)

    def create_widgets(self):
        # 1. Cấu hình AI
        render_frame = tk.LabelFrame(self, text="1. Cấu hình AI (Google Gemini)", padx=10, pady=10)
        render_frame.pack(fill="x", padx=10, pady=5)
        
        status = "Đã nhận API Key" if self.api_key else "Chưa có API Key (Cần file settings.json)"
        color = "blue" if self.api_key else "red"
        tk.Label(render_frame, text=f"Trạng thái: {status}", fg=color, font=("Arial", 9, "bold")).pack(anchor="w")

        # 2. Prompt
        prompt_frame = tk.LabelFrame(self, text="2. Prompt Template", padx=10, pady=10)
        prompt_frame.pack(fill="x", padx=10, pady=5)
        self.prompt_input = scrolledtext.ScrolledText(prompt_frame, height=3, width=80)
        self.prompt_input.pack(fill="x")
        self.prompt_input.insert(tk.END, "Create a highly detailed image for song title: '{title}'.")

        # 3. Quản lý Hiệu ứng (Đã khôi phục đầy đủ tính năng)
        eff_frame = tk.LabelFrame(self, text="3. Quản lý Hiệu ứng", padx=10, pady=10)
        eff_frame.pack(fill="x", padx=10, pady=5)
        
        # -- Bảng danh sách hiệu ứng --
        columns = ("file", "start", "end", "type")
        self.tree = ttk.Treeview(eff_frame, columns=columns, show="headings", height=4)
        
        self.tree.heading("file", text="Tên File")
        self.tree.heading("start", text="Bắt đầu (s)")
        self.tree.heading("end", text="Kết thúc (s)")
        self.tree.heading("type", text="Loại")
        
        self.tree.column("file", width=200)
        self.tree.column("start", width=80, anchor="center")
        self.tree.column("end", width=80, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        
        self.tree.pack(side="left", fill="x", expand=True)
        
        # Scrollbar cho bảng
        scrollbar = ttk.Scrollbar(eff_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # -- Các nút chức năng --
        btn_pnl = tk.Frame(eff_frame)
        btn_pnl.pack(side="bottom", fill="x", pady=5)
        
        tk.Button(btn_pnl, text="+ Thêm Hiệu ứng", command=self.add_effect, bg="#e3f2fd").pack(side="left", padx=5)
        tk.Button(btn_pnl, text="- Xóa Chọn", command=self.remove_effect, bg="#ffcdd2").pack(side="left", padx=5)
        tk.Button(btn_pnl, text="Xóa Tất cả", command=self.clear_effects).pack(side="left", padx=5)

        # 4. Đường dẫn
        path_frame = tk.LabelFrame(self, text="4. Đường dẫn", padx=10, pady=10)
        path_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(path_frame, text="Input Folder", command=self.select_input).grid(row=0, column=0, sticky="w")
        self.lbl_input = tk.Label(path_frame, text="...", anchor="w")
        self.lbl_input.grid(row=0, column=1, sticky="w", padx=5)
        
        tk.Button(path_frame, text="Output Folder", command=self.select_output).grid(row=1, column=0, sticky="w")
        self.lbl_output = tk.Label(path_frame, text="...", anchor="w")
        self.lbl_output.grid(row=1, column=1, sticky="w", padx=5)
        path_frame.columnconfigure(1, weight=1)

        # 5. Log
        log_frame = tk.LabelFrame(self, text="Tiến trình", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=10)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=6, state='disabled')
        self.log_area.pack(fill="both", expand=True)

        self.btn_run = tk.Button(self, text="BẮT ĐẦU", bg="green", fg="white", font=("Arial", 10, "bold"), command=self.start_process)
        self.btn_run.pack(fill="x", padx=20, pady=10)

    # --- Events ---
    def select_input(self):
        f = filedialog.askdirectory()
        if f: self.input_dir = f; self.lbl_input.config(text=f)
    
    def select_output(self):
        f = filedialog.askdirectory()
        if f: self.output_dir = f; self.lbl_output.config(text=f)
    
    # --- LOGIC HIỆU ỨNG (MỚI KHÔI PHỤC) ---
    def add_effect(self):
        files = filedialog.askopenfilenames(filetypes=[("Media", "*.mp4 *.mov *.png *.jpg")])
        if not files: return
        
        # Tạo cửa sổ popup để nhập thời gian
        popup = tk.Toplevel(self)
        popup.title("Cấu hình Hiệu ứng")
        popup.geometry("300x200")
        
        tk.Label(popup, text="Thời gian bắt đầu (giây):").pack(pady=5)
        start_entry = tk.Entry(popup)
        start_entry.insert(0, "0")
        start_entry.pack()
        
        tk.Label(popup, text="Thời gian kết thúc (giây):\n(Để 0 = Hết bài)").pack(pady=5)
        end_entry = tk.Entry(popup)
        end_entry.insert(0, "0")
        end_entry.pack()
        
        def confirm():
            try:
                s = float(start_entry.get())
                e = float(end_entry.get())
            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập số!")
                return
            
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                eff_type = "Overlay" if ext in ['.png', '.jpg'] else "Video"
                
                # Thêm vào list dữ liệu
                self.custom_effects.append({'path': f, 'start': s, 'end': e})
                
                # Hiển thị lên bảng
                display_end = str(e) if e > 0 else "Hết bài"
                self.tree.insert("", "end", values=(os.path.basename(f), s, display_end, eff_type))
            
            popup.destroy()
            
        tk.Button(popup, text="Xác nhận", command=confirm, bg="green", fg="white").pack(pady=20)

    def remove_effect(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Chú ý", "Chưa chọn hiệu ứng nào để xóa!")
            return
            
        for item in selected_items:
            # Lấy thông tin file từ dòng đang chọn
            vals = self.tree.item(item)['values']
            filename = vals[0]
            
            # Xóa khỏi list dữ liệu (Tìm item đầu tiên khớp tên file)
            for eff in self.custom_effects:
                if os.path.basename(eff['path']) == filename:
                    self.custom_effects.remove(eff)
                    break
            
            # Xóa khỏi giao diện
            self.tree.delete(item)

    def clear_effects(self):
        self.tree.delete(*self.tree.get_children())
        self.custom_effects.clear()

    # --- LOGIC CHẠY ---
    def start_process(self):
        self.api_key = self.config_manager.get("api_key")
        
        if not self.input_dir or not self.output_dir:
            messagebox.showerror("Lỗi", "Thiếu thư mục Input/Output")
            return
        
        if not self.api_key:
            messagebox.showerror("Lỗi", "Không tìm thấy API Key trong settings.json!")
            return

        Thread(target=self.process_workflow).start()

    def process_workflow(self):
        self.btn_run.config(state="disabled")
        logging.info("--- BẮT ĐẦU XỬ LÝ (ENGINE: GEMINI) ---")
        
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.m4a', '*.flac']:
            audio_files.extend(glob.glob(os.path.join(self.input_dir, ext)))
        
        total = len(audio_files)
        success = 0
        
        app_path = ServiceManager.get_app_path()
        font_path = os.path.join(app_path, "arial.ttf")

        for idx, audio_path in enumerate(audio_files):
            filename = os.path.basename(audio_path)
            basename = os.path.splitext(filename)[0]
            out_path = os.path.join(self.output_dir, f"{basename}.mp4")
            
            logging.info(f"[{idx+1}/{total}] Đang xử lý: {filename}")
            
            if os.path.exists(out_path):
                logging.warning(f"File tồn tại -> Bỏ qua.")
                continue

            img_path = os.path.join(app_path, "temp_bg.png")
            try:
                prompt_tpl = self.prompt_input.get("1.0", tk.END).strip()
                prompt = prompt_tpl.replace("{title}", basename.replace("_", " "))
                
                logging.info(f"Đang tạo ảnh với Google Gemini...")
                
                # Gọi Gemini API
                data = ServiceManager.gen_gemini(self.api_key, prompt)
                
                with open(img_path, "wb") as f: f.write(data)

                logging.info("Đang render video...")
                # Truyền danh sách self.custom_effects (đã có start/end) vào
                res = ServiceManager.render_video(img_path, audio_path, out_path, self.custom_effects, font_path)
                
                if res.returncode == 0:
                    logging.info("-> Xong!")
                    success += 1
                else:
                    logging.error(f"Lỗi Render: {res.stderr.decode('utf-8')[-100:]}")

            except Exception as e:
                logging.error(f"LỖI: {e}")
            
            if os.path.exists(img_path): os.remove(img_path)

        self.btn_run.config(state="normal")
        logging.info(f"Hoàn tất: {success}/{total} file.")
        messagebox.showinfo("Xong", "Đã xử lý xong.")