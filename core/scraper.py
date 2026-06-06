import requests
from bs4 import BeautifulSoup
import time

class Scraper:
    # 위비티 카테고리 매핑
    CATEGORY_MAP = {
        '20': 'IT/SW/게임',
        '21': '디자인/웹툰',
        '22': '마케팅/아이디어',
        '23': '영상/UCC/사진',
        '24': '예체능/미술/음악',
        '25': '문학/글/시나리오',
        '27': '네이밍/슬로건',
        '28': '건축/건설',
        '29': '과학/공학',
        '10': '대외활동/서포터즈'
    }

    def __init__(self):
        self.base_url = "https://www.wevity.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        }

    def _get_gubun(self, category_code):
        """카테고리 코드에 따라 구분값(1:공모전, 2:대외활동)을 반환"""
        if category_code == '10': # 대외활동/서포터즈
            return '2'
        return '1' # 기본값은 공모전

    def get_max_page_index(self, category_code='20'):
        """해당 카테고리(또는 전체)의 전체 페이지 수를 파악합니다."""
        try:
            gubun = self._get_gubun(category_code)
            
            # URL 생성 분기: 전체보기('all') vs 특정 카테고리
            if category_code == 'all':
                url = f"{self.base_url}?c=find&s=1&gubun={gubun}"
            else:
                url = f"{self.base_url}?c=find&s=1&gubun={gubun}&cidx={category_code}"

            response = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            max_page = 1
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'gp=' in href:
                    # 현재 카테고리 맥락에 맞는 페이지네이션인지 확인
                    if category_code != 'all' and f'cidx={category_code}' not in href:
                        continue
                    
                    try:
                        parts = href.split('gp=')
                        if len(parts) > 1:
                            val = parts[1].split('&')[0]
                            if val.isdigit():
                                page_num = int(val)
                                if page_num > max_page:
                                    max_page = page_num
                    except:
                        continue
            return max_page
        except Exception:
            return 5 

    def get_contest_list(self, category_code='20', pages=1):
        """지정된 카테고리(또는 전체)와 페이지 수만큼 공모전 목록을 가져옵니다."""
        results = []
        
        # 카테고리 이름 설정
        if category_code == 'all':
            category_name = '전체'
        else:
            category_name = self.CATEGORY_MAP.get(category_code, '기타')
        
        # gubun 파라미터 결정
        gubun = self._get_gubun(category_code)

        for page in range(1, pages + 1):
            # URL 생성
            if category_code == 'all':
                target_url = f"{self.base_url}?c=find&s=1&gubun={gubun}&gp={page}"
            else:
                target_url = f"{self.base_url}?c=find&s=1&gubun={gubun}&cidx={category_code}&gp={page}"

            try:
                response = requests.get(target_url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                titles = soup.select('.tit a')
                if not titles: break

                for title_tag in titles:
                    try:
                        title = title_tag.get_text(strip=True)
                        link = self.base_url + title_tag['href']
                        
                        parent_li = title_tag.find_parent('li')
                        if not parent_li: continue

                        organ_tag = parent_li.select_one('.organ')
                        organizer = organ_tag.get_text(strip=True) if organ_tag else "정보 없음"
                        
                        dday_tag = parent_li.select_one('.dday')
                        dday = dday_tag.get_text(strip=True) if dday_tag else "-"

                        # 마감된 공모전 제외
                        if "마감" in dday:
                            continue

                        results.append({
                            'title': title,
                            'category': category_name,
                            'organizer': organizer,
                            'dday': dday,
                            'link': link,
                            'id': link.split('idx=')[-1] if 'idx=' in link else link[-10:]
                        })
                    except:
                        continue
                time.sleep(0.2) 
            except Exception as e:
                print(f"Error: {e}")
        
        return results

    def get_contest_detail(self, wevity_url, max_chars=4000):
        """공모전 상세 페이지의 본문 텍스트를 추출합니다 (AI 초안 생성용 컨텍스트)."""
        try:
            response = requests.get(wevity_url, headers=self.headers, timeout=8)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 본문 영역 후보 (위비티 상세 레이아웃)
            candidates = ['.view-cont', '.cont', '#cont', '.board-view',
                          '.view_con', '.detail', 'article']
            text = ""
            for sel in candidates:
                node = soup.select_one(sel)
                if node:
                    t = node.get_text("\n", strip=True)
                    if len(t) > len(text):
                        text = t
            if not text:
                body = soup.find('body')
                text = body.get_text("\n", strip=True) if body else ""

            # 공백 정리
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            text = "\n".join(lines)
            return text[:max_chars]
        except Exception as e:
            return f"(상세 내용을 가져오지 못했습니다: {e})"

    def get_real_homepage(self, wevity_url):
        try:
            response = requests.get(wevity_url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            candidates = soup.select('li.homepage a, div.btn-set a, .user_files a')
            for btn in candidates:
                href = btn.get('href', '')
                if href.startswith('http') and ('wevity' not in href):
                    return href
            return wevity_url
        except:
            return wevity_url