"""
저장소 계층.

- Supabase가 설정돼 있으면(SUPABASE_URL / SUPABASE_KEY) Supabase(Postgres + Storage) 사용
- 아니면 로컬 JSON 파일(user_data/) 사용  ← 로컬에서 바로 테스트 가능

두 백엔드 모두 동일한 인터페이스(BaseStorage)를 구현한다.

데이터 모델
- profile   : 단일 dict (사용자 프로필)
- projects  : 리스트[dict]; 각 항목에 id, meta(공모전 정보), status, submit_date,
              announce_date, memo, prize, draft 필드
- seen      : 본(=목록에서 제외할) 공모전 id 집합
- hidden    : 숨긴 공모전 리스트[dict]
- files     : 프로젝트별 첨부파일 (이름/바이트)
"""
import os
import io
import json
import uuid
import shutil

from core import config

STORAGE_BUCKET = "attachments"


def new_id():
    return uuid.uuid4().hex[:12]


# --------------------------------------------------------------------------- #
# 공통 인터페이스
# --------------------------------------------------------------------------- #
class BaseStorage:
    backend = "base"

    # ---- 프로필 ----
    def get_profile(self) -> dict: raise NotImplementedError
    def save_profile(self, data: dict): raise NotImplementedError

    # ---- 프로젝트 ----
    def list_projects(self) -> list: raise NotImplementedError
    def get_project(self, pid: str) -> dict: raise NotImplementedError
    def create_project(self, meta: dict):
        """returns (ok: bool, pid_or_msg: str)"""
        raise NotImplementedError
    def update_project(self, pid: str, fields: dict): raise NotImplementedError
    def delete_project(self, pid: str): raise NotImplementedError

    # ---- 본/숨김 ----
    def get_seen(self) -> set: raise NotImplementedError
    def add_seen(self, cid: str): raise NotImplementedError
    def remove_seen(self, cid: str): raise NotImplementedError
    def get_hidden(self) -> list: raise NotImplementedError
    def add_hidden(self, contest: dict): raise NotImplementedError
    def remove_hidden(self, cid: str): raise NotImplementedError

    # ---- 첨부파일 ----
    def list_files(self, pid: str) -> list: raise NotImplementedError
    def add_file(self, pid: str, filename: str, data: bytes): raise NotImplementedError
    def get_file(self, pid: str, filename: str) -> bytes: raise NotImplementedError
    def delete_file(self, pid: str, filename: str): raise NotImplementedError


# --------------------------------------------------------------------------- #
# 로컬 JSON 백엔드
# --------------------------------------------------------------------------- #
class LocalStorage(BaseStorage):
    backend = "local"

    def __init__(self, base_dir="user_data"):
        self.base = base_dir
        self.profile_file = os.path.join(base_dir, "profile.json")
        self.projects_file = os.path.join(base_dir, "projects.json")
        self.seen_file = os.path.join(base_dir, "seen_list.json")
        self.hidden_file = os.path.join(base_dir, "hidden_list.json")
        self.files_dir = os.path.join(base_dir, "files")
        os.makedirs(self.files_dir, exist_ok=True)

    # 내부 헬퍼
    def _read(self, path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _write(self, path, data):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 프로필
    def get_profile(self):
        return self._read(self.profile_file, {})

    def save_profile(self, data):
        self._write(self.profile_file, data)

    # 프로젝트
    def list_projects(self):
        return self._read(self.projects_file, [])

    def get_project(self, pid):
        for p in self.list_projects():
            if p.get("id") == pid:
                return p
        return None

    def create_project(self, meta):
        projects = self.list_projects()
        # 동일 공모전(id) 중복 방지
        cid = meta.get("id")
        if cid and any(p.get("meta", {}).get("id") == cid for p in projects):
            return False, "이미 등록된 공모전입니다."
        pid = new_id()
        projects.append({
            "id": pid,
            "meta": meta,
            "status": "준비중",
            "submit_date": "",
            "announce_date": "",
            "memo": "",
            "prize": "",
            "draft": "",
        })
        self._write(self.projects_file, projects)
        return True, pid

    def update_project(self, pid, fields):
        projects = self.list_projects()
        for p in projects:
            if p.get("id") == pid:
                p.update(fields)
                break
        self._write(self.projects_file, projects)

    def delete_project(self, pid):
        projects = [p for p in self.list_projects() if p.get("id") != pid]
        self._write(self.projects_file, projects)
        # 첨부파일 폴더 삭제
        d = os.path.join(self.files_dir, pid)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)

    # 본/숨김
    def get_seen(self):
        return set(self._read(self.seen_file, []))

    def add_seen(self, cid):
        s = self.get_seen(); s.add(cid)
        self._write(self.seen_file, list(s))

    def remove_seen(self, cid):
        s = self.get_seen(); s.discard(cid)
        self._write(self.seen_file, list(s))

    def get_hidden(self):
        return self._read(self.hidden_file, [])

    def add_hidden(self, contest):
        h = self.get_hidden()
        if not any(x.get("id") == contest.get("id") for x in h):
            h.append(contest)
            self._write(self.hidden_file, h)
        self.add_seen(contest.get("id"))

    def remove_hidden(self, cid):
        h = [x for x in self.get_hidden() if x.get("id") != cid]
        self._write(self.hidden_file, h)
        self.remove_seen(cid)

    # 첨부파일
    def _pdir(self, pid):
        d = os.path.join(self.files_dir, pid)
        os.makedirs(d, exist_ok=True)
        return d

    def list_files(self, pid):
        d = os.path.join(self.files_dir, pid)
        if not os.path.isdir(d):
            return []
        return [{"name": n} for n in sorted(os.listdir(d))]

    def add_file(self, pid, filename, data):
        with open(os.path.join(self._pdir(pid), filename), "wb") as f:
            f.write(data)

    def get_file(self, pid, filename):
        with open(os.path.join(self._pdir(pid), filename), "rb") as f:
            return f.read()

    def delete_file(self, pid, filename):
        p = os.path.join(self._pdir(pid), filename)
        if os.path.exists(p):
            os.remove(p)


# --------------------------------------------------------------------------- #
# Supabase 백엔드
# --------------------------------------------------------------------------- #
class SupabaseStorage(BaseStorage):
    backend = "supabase"

    def __init__(self):
        from supabase import create_client
        self.client = create_client(
            config.get_secret("SUPABASE_URL"),
            config.get_secret("SUPABASE_KEY"),
        )

    # 프로필 (테이블 profile, 단일 행 id=1)
    def get_profile(self):
        res = self.client.table("profile").select("data").eq("id", 1).execute()
        if res.data:
            return res.data[0].get("data") or {}
        return {}

    def save_profile(self, data):
        self.client.table("profile").upsert({"id": 1, "data": data}).execute()

    # 프로젝트
    def list_projects(self):
        res = (self.client.table("projects").select("*")
               .order("created_at", desc=False).execute())
        return res.data or []

    def get_project(self, pid):
        res = self.client.table("projects").select("*").eq("id", pid).execute()
        return res.data[0] if res.data else None

    def create_project(self, meta):
        cid = meta.get("id")
        if cid:
            existing = self.list_projects()
            if any((p.get("meta") or {}).get("id") == cid for p in existing):
                return False, "이미 등록된 공모전입니다."
        row = {
            "meta": meta,
            "status": "준비중",
            "submit_date": "",
            "announce_date": "",
            "memo": "",
            "prize": "",
            "draft": "",
        }
        res = self.client.table("projects").insert(row).execute()
        return True, res.data[0]["id"]

    def update_project(self, pid, fields):
        self.client.table("projects").update(fields).eq("id", pid).execute()

    def delete_project(self, pid):
        self.client.table("projects").delete().eq("id", pid).execute()
        # 첨부파일 정리
        try:
            existing = self.client.storage.from_(STORAGE_BUCKET).list(pid)
            names = [f"{pid}/{f['name']}" for f in existing]
            if names:
                self.client.storage.from_(STORAGE_BUCKET).remove(names)
        except Exception:
            pass

    # 본/숨김
    def get_seen(self):
        res = self.client.table("seen_contests").select("contest_id").execute()
        return {r["contest_id"] for r in (res.data or [])}

    def add_seen(self, cid):
        if cid:
            self.client.table("seen_contests").upsert({"contest_id": cid}).execute()

    def remove_seen(self, cid):
        self.client.table("seen_contests").delete().eq("contest_id", cid).execute()

    def get_hidden(self):
        res = self.client.table("hidden_contests").select("data").execute()
        return [r["data"] for r in (res.data or [])]

    def add_hidden(self, contest):
        cid = contest.get("id")
        self.client.table("hidden_contests").upsert(
            {"contest_id": cid, "data": contest}).execute()
        self.add_seen(cid)

    def remove_hidden(self, cid):
        self.client.table("hidden_contests").delete().eq("contest_id", cid).execute()
        self.remove_seen(cid)

    # 첨부파일 (Storage 버킷)
    def list_files(self, pid):
        try:
            res = self.client.storage.from_(STORAGE_BUCKET).list(pid)
            return [{"name": f["name"]} for f in res if f.get("name")]
        except Exception:
            return []

    def add_file(self, pid, filename, data):
        path = f"{pid}/{filename}"
        self.client.storage.from_(STORAGE_BUCKET).upload(
            path, data, {"upsert": "true"})

    def get_file(self, pid, filename):
        return self.client.storage.from_(STORAGE_BUCKET).download(f"{pid}/{filename}")

    def delete_file(self, pid, filename):
        self.client.storage.from_(STORAGE_BUCKET).remove([f"{pid}/{filename}"])


# --------------------------------------------------------------------------- #
# 팩토리
# --------------------------------------------------------------------------- #
def get_storage() -> BaseStorage:
    if config.supabase_configured():
        try:
            s = SupabaseStorage()
            # 실제 연결/스키마 확인 (실패하면 로컬로 폴백)
            s.client.table("profile").select("id").limit(1).execute()
            return s
        except Exception as e:
            print(f"[storage] Supabase 연결 실패, 로컬로 폴백: {e}")
    return LocalStorage()
