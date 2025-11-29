import customtkinter as ctk

class Navbar(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, width=140, corner_radius=0)
        self.controller = controller
        
        # Logo / Title
        self.logo = ctk.CTkLabel(self, text="TOOLS MULTI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Danh sách các nút menu
        self.buttons = {}
        self.create_nav_button("Làm Video", "video", 1)
        self.create_nav_button("Tạo Phụ Đề", "subtitle", 2)
        self.create_nav_button("Cài Đặt", "settings", 3)
        
        # Spacer để đẩy cài đặt xuống dưới (nếu muốn)
        self.grid_rowconfigure(5, weight=1)

    def create_nav_button(self, text, page_name, row_idx):
        btn = ctk.CTkButton(
            self, 
            text=text, 
            fg_color="transparent", 
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=lambda: self.controller.switch_page(page_name)
        )
        btn.grid(row=row_idx, column=0, sticky="ew", padx=10, pady=5)
        self.buttons[page_name] = btn

    def update_active_button(self, page_name):
        """Đổi màu nút đang được chọn"""
        for name, btn in self.buttons.items():
            if name == page_name:
                btn.configure(fg_color=("gray75", "gray25")) # Màu active
            else:
                btn.configure(fg_color="transparent") # Màu thường