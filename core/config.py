"""
설정/시크릿 로딩.

우선순위: Streamlit secrets(st.secrets) -> 환경변수(os.environ).
로컬에서는 .streamlit/secrets.toml 또는 환경변수로,
클라우드(Streamlit Cloud)에서는 Secrets 설정으로 주입한다.
"""
import os

_DEF = object()


def get_secret(key, default=None):
    # 1) Streamlit secrets
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # 2) 환경변수
    val = os.environ.get(key, _DEF)
    if val is not _DEF:
        return val
    return default


def _is_ascii(s):
    try:
        str(s).encode("ascii")
        return True
    except Exception:
        return False


def supabase_configured():
    """진짜 값이 들어왔을 때만 True. (예시/placeholder/한글 값은 무시 → 로컬 폴백)"""
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key:
        return False
    url, key = str(url), str(key)
    # HTTP 헤더로 들어가므로 ascii가 아니면 사용 불가
    if not _is_ascii(url) or not _is_ascii(key):
        return False
    # 흔한 placeholder 패턴 거르기
    bad = ("xxxx", "...", "(", "여기", "your", "YOUR")
    if any(b in url for b in bad) or any(b in key for b in bad):
        return False
    if not url.startswith("http"):
        return False
    return True


def anthropic_configured():
    return bool(get_secret("ANTHROPIC_API_KEY"))


# AI 모델 (필요시 secrets에서 덮어쓰기 가능)
def recommend_model():
    return get_secret("RECOMMEND_MODEL", "claude-sonnet-4-6")


def draft_model():
    return get_secret("DRAFT_MODEL", "claude-opus-4-8")
