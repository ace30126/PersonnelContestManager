import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import ContestApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 윈도우 생성 및 표시
    window = ContestApp()
    window.show()
    
    sys.exit(app.exec())