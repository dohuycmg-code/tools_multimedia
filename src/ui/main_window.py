import customtkinter as ctk
from src.config.settings import APP_NAME, WINDOW_SIZE
from src.ui.components.navbar import Navbar

from src.ui.pages.video_page import VideoPage
from src.ui.pages.subtitle_page import SubtitlesPage
from src.ui.pages.settings_page import SettingsPage

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- Cấu hình Window ---
        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # --- Bố cục chính (Grid Layout mạnh mẽ hơn Pack cho responsive) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Sidebar (Menu trái)
        # controller=self để Navbar có thể gọi hàm switch_page của MainWindow
        self.sidebar = Navbar(self, controller=self) 
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 2. Content Area (Nội dung phải)
        self.container = ctk.CTkFrame(self, fg_color="transparent") # transparent để ăn theo nền app
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Dictionary chứa Class của các trang
        self.pages = {
            "video": VideoPage,
            "subtitle": SubtitlesPage,
            "settings": SettingsPage
        }
        
        # Mở trang mặc định
        self.switch_page("video")

    def switch_page(self, page_name):
        """Hàm chuyển trang: Xóa trang cũ, load trang mới"""
        
        # 1. Dọn dẹp container cũ
        for widget in self.container.winfo_children():
            widget.destroy()
            
        # 2. Lấy class từ dictionary
        page_class = self.pages.get(page_name)
        
        # 3. Khởi tạo và hiển thị trang mới
        if page_class:
            # Truyền self.container làm cha
            new_page = page_class(self.container) 
            new_page.pack(fill="both", expand=True)
            
            # Cập nhật trạng thái nút bấm bên Sidebar (Optional)
            if hasattr(self.sidebar, 'update_active_button'):
                self.sidebar.update_active_button(page_name)