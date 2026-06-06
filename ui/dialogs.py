import os
import shutil
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QFormLayout, QComboBox, 
                             QDateEdit, QTextEdit, QListWidget, QFileDialog, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView) # QTableWidget 관련 추가
from PyQt6.QtCore import QDate, Qt

# ... [기존 ProjectDetailDialog 클래스는 그대로 유지] ...
class ProjectDetailDialog(QDialog):
    def __init__(self, project_data, data_manager, parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.dm = data_manager
        self.project_path = project_data['folder_path']
        self.files_dir = os.path.join(self.project_path, "files")
        
        self.setWindowTitle(f"프로젝트 관리 - {project_data['meta']['title']}")
        self.resize(600, 700)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. 기본 정보 그룹
        info_group = QGroupBox("공모전 정보")
        info_layout = QFormLayout()
        
        self.lbl_title = QLabel(self.project_data['meta']['title'])
        self.lbl_organizer = QLabel(self.project_data['meta']['organizer'])
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #007bff;")
        
        info_layout.addRow("제목:", self.lbl_title)
        info_layout.addRow("주최사:", self.lbl_organizer)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 2. 상태 및 일정 관리
        status_group = QGroupBox("진행 상태 및 일정")
        status_layout = QFormLayout()
        
        self.combo_status = QComboBox()
        self.combo_status.addItems(["준비중", "제출완료", "발표대기", "수상성공", "아쉬움(탈락)"])
        
        self.date_submit = QDateEdit()
        self.date_submit.setCalendarPopup(True)
        self.date_submit.setDisplayFormat("yyyy-MM-dd")
        
        status_layout.addRow("진행 상태:", self.combo_status)
        status_layout.addRow("제출(예정)일:", self.date_submit)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 3. 첨부파일 관리
        file_group = QGroupBox("첨부파일 관리 (더블클릭하여 열기)")
        file_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.itemDoubleClicked.connect(self.open_file)
        
        btn_file_layout = QHBoxLayout()
        btn_add_file = QPushButton("파일 추가")
        btn_add_file.clicked.connect(self.add_file)
        btn_del_file = QPushButton("선택 파일 삭제")
        btn_del_file.clicked.connect(self.delete_file)
        btn_open_folder = QPushButton("폴더 열기")
        btn_open_folder.clicked.connect(self.open_folder)
        
        btn_file_layout.addWidget(btn_add_file)
        btn_file_layout.addWidget(btn_del_file)
        btn_file_layout.addWidget(btn_open_folder)
        
        file_layout.addWidget(self.file_list)
        file_layout.addLayout(btn_file_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 4. 메모
        memo_group = QGroupBox("메모")
        memo_layout = QVBoxLayout()
        self.text_memo = QTextEdit()
        memo_layout.addWidget(self.text_memo)
        memo_group.setLayout(memo_layout)
        layout.addWidget(memo_group)

        # 저장 버튼
        btn_save = QPushButton("변경사항 저장")
        btn_save.setObjectName("primary_btn")
        btn_save.setMinimumHeight(40)
        btn_save.clicked.connect(self.save_changes)
        layout.addWidget(btn_save)

    def load_data(self):
        status = self.project_data.get('status', '준비중')
        idx = self.combo_status.findText(status)
        if idx >= 0: self.combo_status.setCurrentIndex(idx)
        
        submit_date = self.project_data.get('schedule', {}).get('submit_date', '')
        if submit_date and submit_date != '-':
            self.date_submit.setDate(QDate.fromString(submit_date, "yyyy-MM-dd"))
        else:
            self.date_submit.setDate(QDate.currentDate())
            
        self.text_memo.setPlainText(self.project_data.get('memo', ''))
        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.clear()
        if os.path.exists(self.files_dir):
            files = os.listdir(self.files_dir)
            for f in files:
                self.file_list.addItem(f)

    def add_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "파일 선택", "", "All Files (*)")
        if not file_paths: return
        if not os.path.exists(self.files_dir): os.makedirs(self.files_dir)
        for path in file_paths:
            try:
                fname = os.path.basename(path)
                shutil.copy2(path, os.path.join(self.files_dir, fname))
            except Exception as e:
                QMessageBox.warning(self, "오류", f"파일 복사 실패: {e}")
        self.refresh_file_list()

    def delete_file(self):
        item = self.file_list.currentItem()
        if not item: return
        fname = item.text()
        file_path = os.path.join(self.files_dir, fname)
        if QMessageBox.question(self, "삭제 확인", f"정말 '{fname}' 파일을 삭제하시겠습니까?", 
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.warning(self, "오류", f"삭제 실패: {e}")

    def open_file(self, item):
        fname = item.text()
        file_path = os.path.join(self.files_dir, fname)
        try: os.startfile(file_path)
        except Exception as e: QMessageBox.warning(self, "오류", f"열기 실패: {e}")

    def open_folder(self):
        try: os.startfile(self.files_dir)
        except: pass

    def save_changes(self):
        self.project_data['status'] = self.combo_status.currentText()
        self.project_data['schedule']['submit_date'] = self.date_submit.date().toString("yyyy-MM-dd")
        self.project_data['memo'] = self.text_memo.toPlainText()
        try:
            self.dm.save_project_info(self.project_path, self.project_data)
            QMessageBox.information(self, "저장 완료", "프로젝트 정보가 업데이트되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"에러가 발생했습니다: {e}")


# --- [NEW] 숨긴 공모전 관리 다이얼로그 ---
class ManageHiddenDialog(QDialog):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.dm = data_manager
        self.setWindowTitle("숨긴 공모전 관리 (복구)")
        self.resize(700, 500)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("체크박스를 선택하고 '복구' 버튼을 누르면, 해당 공모전이 다시 검색 목록에 나타납니다.")
        lbl_info.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(lbl_info)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["선택", "제목", "주최사", "D-Day"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_restore = QPushButton("선택 항목 복구 (숨기기 취소)")
        btn_restore.setObjectName("primary_btn") # 스타일 적용
        btn_restore.clicked.connect(self.restore_selected)
        
        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_restore)
        btn_layout.addStretch(1)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def load_data(self):
        self.hidden_list = self.dm.get_hidden_contests()
        self.table.setRowCount(0)
        
        for i, item in enumerate(self.hidden_list):
            self.table.insertRow(i)
            
            # 체크박스 아이템
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            chk_item.setData(Qt.ItemDataRole.UserRole, item['id']) # ID 저장
            
            self.table.setItem(i, 0, chk_item)
            self.table.setItem(i, 1, QTableWidgetItem(item.get('title', '제목 없음')))
            self.table.setItem(i, 2, QTableWidgetItem(item.get('organizer', '-')))
            self.table.setItem(i, 3, QTableWidgetItem(item.get('dday', '-')))

    def restore_selected(self):
        restored_count = 0
        ids_to_restore = []

        # 체크된 항목 수집
        for row in range(self.table.rowCount()):
            chk_item = self.table.item(row, 0)
            if chk_item.checkState() == Qt.CheckState.Checked:
                contest_id = chk_item.data(Qt.ItemDataRole.UserRole)
                ids_to_restore.append(contest_id)

        if not ids_to_restore:
            QMessageBox.warning(self, "알림", "복구할 항목을 선택해주세요.")
            return

        # 복구 진행
        for cid in ids_to_restore:
            self.dm.restore_contest(cid)
            restored_count += 1
        
        QMessageBox.information(self, "완료", f"{restored_count}개의 항목이 복구되었습니다.\n다시 검색하시면 목록에 나타납니다.")
        self.load_data() # 리스트 갱신