import os
import webbrowser
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, 
                             QLabel, QMessageBox, QHeaderView, QInputDialog, 
                             QProgressDialog, QDialog, QComboBox, QAbstractItemView) # QAbstractItemView 추가
from PyQt6.QtGui import QIcon, QColor, QFont
from PyQt6.QtCore import Qt, QCoreApplication

from core.scraper import Scraper
from core.data_manager import DataManager
from core.worker import ScrapingWorker
# ManageHiddenDialog 추가
from ui.dialogs import ProjectDetailDialog, ManageHiddenDialog
from ui.styles import get_main_stylesheet

class ContestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("나만의 공모전 매니저")
        self.resize(1150, 750) 
        
        self.set_app_icon()

        self.scraper = Scraper()
        self.db = DataManager()
        self.current_contest_list = []

        self.init_ui()
        self.setStyleSheet(get_main_stylesheet())

    def set_app_icon(self):
        icon_path = "icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 상단 대시보드
        self.dashboard_label = QLabel("준비 완료")
        self.dashboard_label.setStyleSheet("""
            QLabel {
                background-color: white; 
                padding: 15px; 
                border-radius: 8px; 
                border: 1px solid #dee2e6;
                font-size: 15px;
                font-weight: bold;
                color: #212529;
            }
        """)
        layout.addWidget(self.dashboard_label)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        self.search_tab = QWidget()
        self.init_search_tab()
        tabs.addTab(self.search_tab, "🔍 공모전 탐색")

        self.my_project_tab = QWidget()
        self.init_project_tab()
        tabs.addTab(self.my_project_tab, "📂 내 프로젝트 관리")

        self.update_dashboard()

    def init_search_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 컨트롤 패널
        control_layout = QHBoxLayout()
        
        self.combo_category = QComboBox()
        self.combo_category.setMinimumWidth(150)
        self.combo_category.setStyleSheet("padding: 5px; font-weight: bold;")
        
        self.combo_category.addItem("전체보기 (All)", "all")
        for code, name in Scraper.CATEGORY_MAP.items():
            self.combo_category.addItem(name, code)
        
        self.btn_refresh = QPushButton("선택 분야 검색")
        self.btn_refresh.setObjectName("primary_btn")
        self.btn_refresh.clicked.connect(self.load_contests)

        self.btn_add_project = QPushButton("참가하기")
        self.btn_add_project.clicked.connect(self.add_to_my_projects)
        
        self.btn_hide = QPushButton("선택 항목 숨기기")
        self.btn_hide.clicked.connect(self.hide_contest)

        # [NEW] 숨긴 항목 관리 버튼
        self.btn_manage_hidden = QPushButton("숨긴 항목 관리")
        self.btn_manage_hidden.setStyleSheet("color: #666;")
        self.btn_manage_hidden.clicked.connect(self.open_hidden_manager)
        
        control_layout.addWidget(QLabel("분야 선택:"))
        control_layout.addWidget(self.combo_category)
        control_layout.addWidget(self.btn_refresh)
        control_layout.addStretch(1)
        control_layout.addWidget(self.btn_add_project)
        control_layout.addWidget(self.btn_hide)
        control_layout.addWidget(self.btn_manage_hidden) # 버튼 추가
        
        layout.addLayout(control_layout)

        # 테이블 영역
        self.search_table = QTableWidget()
        self.search_table.setColumnCount(5) 
        self.search_table.setHorizontalHeaderLabels(["분야", "제목", "주최사", "D-Day", "상태"])
        
        self.search_table.setAlternatingRowColors(True)
        self.search_table.setShowGrid(False)
        self.search_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # [NEW] 다중 선택 모드 활성화 (ExtendedSelection: Ctrl+Click, Shift+Click, 드래그 지원)
        self.search_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        header = self.search_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.search_table.setColumnWidth(4, 60)

        self.search_table.cellDoubleClicked.connect(self.on_table_double_click)

        layout.addWidget(self.search_table)
        self.search_tab.setLayout(layout)

    def init_project_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.project_table = QTableWidget()
        self.project_table.setColumnCount(4)
        self.project_table.setHorizontalHeaderLabels(["프로젝트명", "진행상태", "접수일", "메모"])
        
        self.project_table.setAlternatingRowColors(True)
        self.project_table.setShowGrid(False)
        self.project_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.project_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        header = self.project_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        self.project_table.cellDoubleClicked.connect(self.on_project_double_click)

        layout.addWidget(self.project_table)
        
        btn_layout = QHBoxLayout()
        
        btn_refresh = QPushButton("목록 갱신")
        btn_refresh.clicked.connect(self.load_my_projects)
        
        self.btn_delete_project = QPushButton("선택 프로젝트 삭제")
        self.btn_delete_project.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.btn_delete_project.clicked.connect(self.delete_project)

        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_delete_project)
        
        layout.addLayout(btn_layout)
        
        self.my_project_tab.setLayout(layout)

    def update_dashboard(self):
        projects = self.db.get_my_projects()
        count = len(projects)
        ongoing = sum(1 for p in projects if p['status'] == '준비중')
        
        text = f"""
        <html>
            <body>
                <span style='font-size:16px; color:#555;'>현재 관리 중인 프로젝트</span><br>
                <span style='font-size:24px; color:#007bff; font-weight:bold;'>{count}</span>
                <span style='font-size:16px; color:#333;'>개</span>
                &nbsp;&nbsp;
                <span style='color:#888;'>(진행중: <span style='color:#28a745; font-weight:bold;'>{ongoing}</span>)</span>
            </body>
        </html>
        """
        self.dashboard_label.setText(text)
        self.load_my_projects()

    def load_contests(self):
        category_code = self.combo_category.currentData()
        category_name = self.combo_category.currentText()

        self.dashboard_label.setText(f"'{category_name}' 정보 확인 중...")
        QCoreApplication.processEvents()
        
        max_page = self.scraper.get_max_page_index(category_code)
        
        msg = f"'{category_name}' 목록은 총 {max_page}페이지가 있습니다.\n몇 페이지까지 탐색하시겠습니까?"
        default_val = min(5, max_page)
        
        pages, ok = QInputDialog.getInt(self, "탐색 범위 설정", msg, default_val, 1, max_page, 1)
        if not ok:
            self.dashboard_label.setText("탐색이 취소되었습니다.")
            self.update_dashboard()
            return

        self.progress_dialog = QProgressDialog("데이터 수집 중...\n(잠시만 기다려주세요)", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("데이터 수집")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setRange(0, 0)
        self.progress_dialog.setCancelButton(None)
        
        self.progress_dialog.setStyleSheet("""
            QProgressDialog { background-color: white; color: black; }
            QLabel { color: black; background: transparent; font-weight: bold; }
            QProgressBar { color: black; }
        """)
        self.progress_dialog.show()

        self.worker = ScrapingWorker(self.scraper, category_code, pages)
        self.worker.data_loaded.connect(self.on_scraping_finished)
        self.worker.start()

    def on_scraping_finished(self, raw_data):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if not raw_data:
            QMessageBox.warning(self, "결과 없음", "데이터를 가져오지 못했습니다.")
            self.update_dashboard()
            return

        seen_list = self.db.get_seen_list()
        self.current_contest_list = []
        
        self.search_table.setRowCount(0)
        
        row = 0
        for item in raw_data:
            if item['id'] in seen_list:
                continue
            
            self.current_contest_list.append(item)
            self.search_table.insertRow(row)
            
            cate_item = QTableWidgetItem(item['category'])
            title_item = QTableWidgetItem(item['title'])
            organ_item = QTableWidgetItem(item['organizer'])
            dday_item = QTableWidgetItem(item['dday'])
            status_item = QTableWidgetItem("신규")
            
            cate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            organ_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dday_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            d_text = item['dday'].replace(" ", "")
            if d_text.upper() == "D-DAY" or "TODAY" in d_text.upper():
                dday_item.setForeground(QColor("#dc3545"))
                dday_item.setFont(QFont("Malgun Gothic", 9, QFont.Weight.Bold))
            elif d_text.startswith("D-"):
                try:
                    days_left = int(d_text.split("-")[1])
                    if days_left <= 7:
                        dday_item.setForeground(QColor("#dc3545"))
                        dday_item.setFont(QFont("Malgun Gothic", 9, QFont.Weight.Bold))
                except:
                    pass

            self.search_table.setItem(row, 0, cate_item)
            self.search_table.setItem(row, 1, title_item)
            self.search_table.setItem(row, 2, organ_item)
            self.search_table.setItem(row, 3, dday_item)
            self.search_table.setItem(row, 4, status_item)
            
            self.search_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item)
            row += 1
            
        self.dashboard_label.setText(f"✅ 탐색 완료: 새로운 공모전 {row}개 발견")
        if row == 0:
             self.update_dashboard()

    def on_table_double_click(self, row, col):
        item = self.search_table.item(row, 0)
        contest_data = item.data(Qt.ItemDataRole.UserRole)
        if contest_data:
            self.dashboard_label.setText(f"사이트 연결 중... {contest_data['title']}")
            QCoreApplication.processEvents()
            
            real_url = self.scraper.get_real_homepage(contest_data['link'])
            webbrowser.open(real_url)
            self.dashboard_label.setText("준비 완료")
            self.update_dashboard()

    def add_to_my_projects(self):
        rows = sorted(set(index.row() for index in self.search_table.selectedIndexes()))
        if not rows: 
            QMessageBox.warning(self, "알림", "목록에서 공모전을 선택해주세요.")
            return
        
        added_count = 0
        for row in rows:
            item = self.search_table.item(row, 0)
            contest_data = item.data(Qt.ItemDataRole.UserRole)
            
            success, msg = self.db.create_project(contest_data)
            if success:
                self.db.add_to_seen(contest_data['id'])
                added_count += 1
        
        # UI 갱신 (선택된 행들 제거 - 역순으로 제거해야 인덱스 안 꼬임)
        for row in reversed(rows):
            self.search_table.removeRow(row)

        if added_count > 0:
            QMessageBox.information(self, "성공", f"총 {added_count}개의 프로젝트가 생성되었습니다.")
            self.update_dashboard()

    def hide_contest(self):
        """[NEW] 다중 선택 숨기기 기능"""
        # 선택된 행 인덱스 가져오기 (중복 제거 및 정렬)
        selected_rows = sorted(set(index.row() for index in self.search_table.selectedIndexes()), reverse=True)
        
        if not selected_rows:
             QMessageBox.warning(self, "알림", "숨길 항목을 선택해주세요.")
             return

        # 확인 메시지 (다중 선택 시에만 띄움, 1개는 그냥 바로 숨김)
        if len(selected_rows) > 1:
            reply = QMessageBox.question(self, "숨기기 확인", f"선택한 {len(selected_rows)}개 항목을 숨기시겠습니까?", 
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        for row in selected_rows:
            item = self.search_table.item(row, 0)
            contest_data = item.data(Qt.ItemDataRole.UserRole)
            
            # [변경] 단순 seen_list 추가가 아니라, hidden_list에 저장 (복구 가능하도록)
            self.db.archive_contest(contest_data)
            
            # 테이블에서 제거
            self.search_table.removeRow(row)

    def open_hidden_manager(self):
        """[NEW] 숨긴 항목 관리 다이얼로그 열기"""
        dialog = ManageHiddenDialog(self.db, self)
        dialog.exec()
        # 다이얼로그 종료 후에는 별도 갱신 없이, 사용자가 필요시 '재검색'하도록 유도

    def load_my_projects(self):
        self.project_table.setRowCount(0)
        projects = self.db.get_my_projects()
        
        for i, p in enumerate(projects):
            self.project_table.insertRow(i)
            
            title_item = QTableWidgetItem(p['meta']['title'])
            status_item = QTableWidgetItem(p['status'])
            s_date = p['schedule'].get('submit_date', '-') or '-'
            date_item = QTableWidgetItem(s_date)
            memo_item = QTableWidgetItem(p.get('memo', ''))
            
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.project_table.setItem(i, 0, title_item)
            self.project_table.setItem(i, 1, status_item)
            self.project_table.setItem(i, 2, date_item)
            self.project_table.setItem(i, 3, memo_item)
            
            self.project_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, p)

    def on_project_double_click(self, row, col):
        item = self.project_table.item(row, 0)
        project_data = item.data(Qt.ItemDataRole.UserRole)
        if project_data:
            dialog = ProjectDetailDialog(project_data, self.db, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_my_projects()
                self.update_dashboard()

    def delete_project(self):
        row = self.project_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "알림", "삭제할 프로젝트를 선택해주세요.")
            return

        item = self.project_table.item(row, 0)
        project_data = item.data(Qt.ItemDataRole.UserRole)
        title = project_data['meta']['title']

        reply = QMessageBox.question(self, "삭제 확인", 
                                     f"정말 '{title}' 프로젝트를 삭제하시겠습니까?\n\n"
                                     "삭제된 데이터(첨부파일 포함)는 복구할 수 없습니다.\n"
                                     "(탐색 목록에는 다시 나타납니다)",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.db.delete_project(project_data['folder_path'])
            if success:
                QMessageBox.information(self, "삭제 완료", msg)
                self.load_my_projects()
                self.update_dashboard()
            else:
                QMessageBox.critical(self, "오류", msg)