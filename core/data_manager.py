import os
import json
import shutil
from datetime import datetime

class DataManager:
    def __init__(self):
        self.base_dir = "user_data"
        self.seen_file = os.path.join(self.base_dir, "seen_list.json")
        self.hidden_file = os.path.join(self.base_dir, "hidden_list.json") # [NEW] 숨김 목록 파일
        self.projects_dir = os.path.join(self.base_dir, "projects")
        
        self._init_filesystem()

    def _init_filesystem(self):
        """기본 폴더 및 파일 생성"""
        os.makedirs(self.projects_dir, exist_ok=True)
        # seen_list 초기화
        if not os.path.exists(self.seen_file):
            with open(self.seen_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        # hidden_list 초기화
        if not os.path.exists(self.hidden_file):
            with open(self.hidden_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def get_seen_list(self):
        try:
            with open(self.seen_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()

    def add_to_seen(self, contest_id):
        seen = self.get_seen_list()
        seen.add(contest_id)
        with open(self.seen_file, 'w', encoding='utf-8') as f:
            json.dump(list(seen), f)

    def remove_from_seen(self, contest_id):
        seen = self.get_seen_list()
        if contest_id in seen:
            seen.remove(contest_id)
            with open(self.seen_file, 'w', encoding='utf-8') as f:
                json.dump(list(seen), f)

    # --- [NEW] 숨김 목록 관리 기능 ---
    def get_hidden_contests(self):
        """숨긴 공모전 전체 목록 반환"""
        try:
            with open(self.hidden_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def archive_contest(self, contest_data):
        """공모전을 숨김 목록에 저장하고 seen_list(검색제외)에도 추가"""
        # 1. hidden_list에 전체 데이터 저장 (나중에 복구 시 정보 확인용)
        hidden = self.get_hidden_contests()
        # 중복 체크
        if not any(item['id'] == contest_data['id'] for item in hidden):
            hidden.append(contest_data)
            with open(self.hidden_file, 'w', encoding='utf-8') as f:
                json.dump(hidden, f, indent=4, ensure_ascii=False)
        
        # 2. 검색 목록에서 제외하기 위해 seen_list에도 ID 등록
        self.add_to_seen(contest_data['id'])

    def restore_contest(self, contest_id):
        """숨김 목록에서 제거하고 검색 가능하도록 복구"""
        # 1. hidden_list에서 제거
        hidden = self.get_hidden_contests()
        hidden = [item for item in hidden if item['id'] != contest_id]
        with open(self.hidden_file, 'w', encoding='utf-8') as f:
            json.dump(hidden, f, indent=4, ensure_ascii=False)

        # 2. seen_list에서도 제거 (그래야 검색 시 다시 뜸)
        self.remove_from_seen(contest_id)

    # --- 프로젝트 관리 기능 (기존 유지) ---
    def create_project(self, contest_data):
        safe_title = "".join([c for c in contest_data['title'] if c.isalnum() or c in (' ', '_')]).strip()
        project_path = os.path.join(self.projects_dir, safe_title)
        
        if os.path.exists(project_path):
            return False, "이미 존재하는 프로젝트입니다."
        
        os.makedirs(os.path.join(project_path, "files"), exist_ok=True)
        
        info = {
            "meta": contest_data,
            "status": "준비중", 
            "schedule": {"submit_date": "", "announce_date": ""},
            "memo": "", "prize": ""
        }
        self.save_project_info(project_path, info)
        return True, project_path

    def delete_project(self, project_path):
        try:
            contest_id = None
            json_path = os.path.join(project_path, "info.json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    contest_id = data['meta'].get('id')

            if os.path.exists(project_path):
                shutil.rmtree(project_path)

            if contest_id:
                self.remove_from_seen(contest_id)

            return True, "삭제되었습니다."
        except Exception as e:
            return False, f"삭제 실패: {e}"

    def save_project_info(self, project_path, data):
        with open(os.path.join(project_path, "info.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_my_projects(self):
        projects = []
        if not os.path.exists(self.projects_dir):
            return projects
        for folder in os.listdir(self.projects_dir):
            path = os.path.join(self.projects_dir, folder)
            json_path = os.path.join(path, "info.json")
            if os.path.isfile(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['folder_path'] = path
                        projects.append(data)
                except:
                    continue
        return projects