import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'src'))
from utils.logger import setup_logging

if __name__ == "__main__":
    setup_logging()
    
    from ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()
