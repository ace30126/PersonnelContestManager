def get_main_stylesheet():
    """애플리케이션 전체에 적용될 스타일시트를 반환합니다."""
    return """
        /* 전역 설정: 모든 위젯을 라이트 모드로 강제 */
        QWidget {
            background-color: #ffffff;
            color: #000000;
            font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
        }

        /* 메인 윈도우 배경 (약간 회색) */
        QMainWindow {
            background-color: #f4f6f9; 
        }

        /* 라벨 */
        QLabel {
            color: #333333;
            font-size: 14px;
            background-color: transparent; 
        }

        /* 탭 스타일 */
        QTabWidget::pane {
            border: 1px solid #ced4da;
            background: white;
            border-radius: 4px;
        }
        QTabBar::tab {
            background: #e9ecef;
            border: 1px solid #ced4da;
            padding: 8px 15px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            color: #495057;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white; 
            font-weight: bold;
            color: #007bff; 
        }
        
        /* 버튼 기본 스타일 */
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 5px;
            padding: 8px 12px;
            color: #495057;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #f1f3f5;
            border-color: #adb5bd;
        }
        QPushButton:pressed {
            background-color: #e9ecef;
        }
        
        /* 강조 버튼 */
        QPushButton#primary_btn {
            background-color: #007bff;
            color: white;
            border: 1px solid #0056b3;
            font-weight: bold;
        }
        QPushButton#primary_btn:hover {
            background-color: #0069d9;
        }

        /* 테이블 스타일 */
        QTableWidget {
            background-color: white;
            gridline-color: #dee2e6;
            selection-background-color: #e7f5ff; 
            selection-color: #000000; 
            color: #000000;
            font-size: 13px;
            border: 1px solid #dee2e6;
        }
        QTableWidget::item {
            color: #000000;
        }
        QHeaderView::section {
            background-color: #f8f9fa;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #dee2e6;
            font-weight: bold;
            color: #000000;
        }
        
        /* 다이얼로그 및 메시지 박스 전용 스타일 */
        QDialog, QMessageBox, QInputDialog {
            background-color: #ffffff;
            color: #000000;
        }
        QMessageBox QLabel, QInputDialog QLabel {
            color: #000000;
            background-color: transparent;
        }
        
        /* 그룹박스 스타일 */
        QGroupBox {
            border: 1px solid #ced4da;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        /* 입력 필드 */
        QLineEdit, QSpinBox, QComboBox, QDateEdit, QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #ced4da;
            padding: 4px;
        }
        QListWidget {
            border: 1px solid #ced4da;
            background-color: #ffffff;
            color: #000000;
        }

        /* 프로그레스 바 스타일 */
        QProgressBar {
            border: 1px solid #ced4da;
            border-radius: 5px;
            text-align: center;
            background-color: #e9ecef;
            color: #000000;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: #007bff;
            width: 10px; 
        }

        QProgressDialog {
            background-color: white;
            min-width: 400px;
        }
        QProgressDialog QLabel {
            font-size: 14px;
            font-weight: bold;
            color: #333333;
            padding: 15px;
            background-color: transparent;
        }
    """