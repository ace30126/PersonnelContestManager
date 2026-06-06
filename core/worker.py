from PyQt6.QtCore import QThread, pyqtSignal

class ScrapingWorker(QThread):
    """
    UI 멈춤 방지를 위해 백그라운드에서 스크래핑을 수행하는 워커 클래스
    """
    data_loaded = pyqtSignal(list)

    def __init__(self, scraper, category_code, pages):
        super().__init__()
        self.scraper = scraper
        self.category_code = category_code
        self.pages = pages

    def run(self):
        # 선택된 카테고리와 페이지 수로 데이터 수집
        data = self.scraper.get_contest_list(category_code=self.category_code, pages=self.pages)
        self.data_loaded.emit(data)