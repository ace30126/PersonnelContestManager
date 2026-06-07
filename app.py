"""
공모전 매니저 (웹) — Streamlit

기능
- 프로필 입력/저장
- 공모전 크롤링 탐색 (위비티)
- AI(Claude) 적합도 추천 — 프로필 기반
- 내 프로젝트 관리 (상태/일정/메모/첨부파일)
- AI(Claude) 제출 초안 자동 생성

실행:  streamlit run app.py
"""
import re
import hashlib
import datetime as dt

import pandas as pd
import streamlit as st
import extra_streamlit_components as stx

from core import config
from core.scraper import Scraper
from core.storage import get_storage
from core import ai

st.set_page_config(page_title="공모전 매니저", page_icon="🏆", layout="wide",
                   initial_sidebar_state="collapsed")

# --------------------------------------------------------------------------- #
# 스타일 (대시보드형) — StudyMate 레퍼런스 느낌의 클린 카드 UI
# --------------------------------------------------------------------------- #
ACCENT = "#6C5CE7"
CSS = f"""
<style>
:root {{
    --accent: {ACCENT}; --accent2: #8A7CF8;
    --orange: #F7A23B; --pink: #FF6FA5; --blue: #4D8DEF;
    --green: #2ECC71; --red: #FF5B6E;
    --ink: #2E2E3A; --muted: #9AA0A6; --line: #EEF0F4; --track: #EFF0F5;
}}
.stApp {{ background: #F6F7FB; }}
* {{ font-family: 'Pretendard','Malgun Gothic',-apple-system,'Segoe UI',sans-serif; }}
.block-container {{ padding-top: 3rem; max-width: 1180px; }}

/* 사이드바 */
section[data-testid="stSidebar"] {{ background:#fff; border-right:1px solid var(--line); }}
section[data-testid="stSidebar"] * {{ color: var(--ink); }}
section[data-testid="stSidebar"] label[data-baseweb="radio"] {{
    padding:9px 12px; border-radius:12px; margin-bottom:2px; transition:.15s;
}}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {{ background:#f3f1fe; }}

/* 카드 */
.card {{
    background:#fff; border:1px solid var(--line); border-radius:18px;
    padding:18px 20px; box-shadow:0 4px 16px rgba(30,32,60,.05); margin-bottom:14px;
}}
.card-tight {{ padding:14px 18px; }}

/* 히어로(카운트다운) */
.hero {{
    background:#fff; border:1px solid var(--line); border-radius:22px;
    padding:30px 24px; text-align:center; box-shadow:0 6px 22px rgba(108,92,231,.08);
    margin-bottom:16px;
}}
.hero .pill {{
    display:inline-block; background:#f3f1fe; color:var(--accent);
    padding:6px 14px; border-radius:999px; font-size:13px; font-weight:700; margin-bottom:12px;
}}
.hero .big {{ font-size:64px; font-weight:800; color:var(--ink); line-height:1.05; letter-spacing:1px; }}
.hero .ttl {{ font-size:17px; font-weight:700; color:var(--ink); margin-top:8px; }}
.hero .sub {{ color:var(--muted); font-size:13px; }}

/* 통계 타일 */
.tile {{
    background:#fff; border:1px solid var(--line); border-radius:16px; padding:14px 16px;
    box-shadow:0 4px 16px rgba(30,32,60,.05);
}}
.tile .label {{ font-size:12.5px; color:var(--muted); font-weight:600; }}
.tile .value {{ font-size:26px; font-weight:800; color:var(--ink); }}
.tile .value.p {{ color:var(--accent); }}
.tile .value.r {{ color:var(--red); }}
.tile .value.g {{ color:var(--green); }}

/* 진행/활동 바 */
.barrow {{ display:flex; align-items:center; gap:10px; margin:9px 0; font-size:13px; }}
.barrow .nm {{ width:96px; color:var(--ink); font-weight:600; flex:none; }}
.barrow .val {{ width:54px; text-align:right; color:var(--muted); flex:none; }}
.track {{ flex:1; height:10px; background:var(--track); border-radius:999px; overflow:hidden; }}
.fill {{ height:100%; border-radius:999px; }}

/* 헤더/인사 */
.apphead {{ display:flex; align-items:center; gap:12px; margin-bottom:6px; }}
.apphead .logo {{
    width:42px; height:42px; border-radius:13px; background:linear-gradient(135deg,var(--accent),var(--accent2));
    display:flex; align-items:center; justify-content:center; font-size:22px; box-shadow:0 4px 12px rgba(108,92,231,.3);
}}
.apphead .nm {{ font-size:18px; font-weight:800; color:var(--ink); }}
.apphead .sm {{ font-size:12px; color:var(--muted); }}
.hello {{ color:var(--muted); font-size:14px; margin-top:6px; }}
.hello b {{ display:block; font-size:26px; color:var(--ink); font-weight:800; }}

/* 뱃지 */
.badge {{ display:inline-block; padding:3px 11px; border-radius:999px; font-size:12px; font-weight:700; }}
.b-soon {{ background:#ffe5e8; color:var(--red); }}
.b-ok {{ background:#e6fbf1; color:#12a466; }}
.b-info {{ background:#efeaff; color:var(--accent); }}
.b-gray {{ background:#f1f3f5; color:#868e96; }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:8px; }}

.rec-score {{ font-size:28px; font-weight:800; color:var(--accent); }}
.pagetitle {{ font-size:26px; font-weight:800; color:var(--ink); margin-bottom:2px; line-height:1.4; }}
.apphead .nm {{ line-height:1.4; }}
.subtitle {{ color:var(--muted); margin-bottom:18px; font-size:14px; }}
.sechead {{ font-size:15px; font-weight:800; color:var(--ink); margin:6px 0 8px; }}

/* 버튼/탭/인풋 */
.stButton>button {{ border-radius:12px; font-weight:700; border:1px solid var(--line); }}
div[data-testid="stButton"] button[kind="primary"] {{
    background:var(--accent); border:none; box-shadow:0 4px 12px rgba(108,92,231,.25); }}
.stTabs [data-baseweb="tab-list"] {{ gap:4px; }}
.stTabs [aria-selected="true"] {{ color:var(--accent) !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background:var(--accent); }}
h1,h2,h3 {{ color:var(--ink); }}

/* 사이드바 숨김 (하단 탭바 사용) */
section[data-testid="stSidebar"], div[data-testid="collapsedControl"] {{ display:none !important; }}
.block-container {{ padding-bottom: 96px; }}

/* 하단 탭바 */
.botnav {{
    position:fixed; left:0; right:0; bottom:0; z-index:9999;
    background:#fff; border-top:1px solid var(--line);
    box-shadow:0 -4px 18px rgba(30,32,60,.06);
    display:flex; justify-content:center; gap:46px; padding:9px 0 11px;
}}
.botnav .bn-item {{
    display:flex; flex-direction:column; align-items:center; gap:3px;
    text-decoration:none; color:var(--muted); font-size:11.5px; font-weight:700;
    min-width:62px; transition:.15s;
}}
.botnav .bn-item .ic {{ font-size:21px; filter:grayscale(1) opacity(.55); transition:.15s; }}
.botnav .bn-item:hover {{ color:var(--accent); }}
.botnav .bn-item.active {{ color:var(--accent); }}
.botnav .bn-item.active .ic {{ filter:none; }}
.topstatus {{ text-align:right; color:var(--muted); font-size:12px; }}

/* 클릭 가능한 대시보드 항목 */
a.navlink {{ text-decoration:none; color:inherit; display:block; }}
a.navlink .tile, a.navlink .hero {{ transition:.15s; }}
a.navlink:hover .tile, a.navlink:hover .hero {{
    transform:translateY(-2px); border-color:#d9d2fb;
    box-shadow:0 8px 24px rgba(108,92,231,.16);
}}
a.rowlink {{ text-decoration:none; color:inherit; display:block;
    border-radius:10px; margin:0 -8px; padding:0 8px; transition:.12s; }}
a.rowlink:hover {{ background:#f6f4ff; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def bar_row(name, value_text, pct, color):
    pct = max(2, min(100, pct))
    return (f"<div class='barrow'><div class='nm'>{name}</div>"
            f"<div class='track'><div class='fill' style='width:{pct}%;background:{color}'></div></div>"
            f"<div class='val'>{value_text}</div></div>")


# --------------------------------------------------------------------------- #
# 자원
# --------------------------------------------------------------------------- #
@st.cache_resource
def get_scraper():
    return Scraper()


@st.cache_resource
def get_db():
    return get_storage()


db = get_db()
scraper = get_scraper()

# 쿠키 매니저 (로그인 상태를 브라우저 쿠키로 유지 → 페이지 이동·새로고침에도 안 풀림)
cookie_mgr = stx.CookieManager(key="mcm_cookies")
AUTH_COOKIE = "mcm_auth"


def _auth_token(pw: str) -> str:
    """비밀번호로부터 쿠키에 저장할 토큰 생성(비번 바뀌면 자동 무효화)."""
    return hashlib.sha256(f"mcm::{pw}".encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# 로그인 게이트 (APP_PASSWORD 미설정 시 자동 통과 = 로컬용)
# --------------------------------------------------------------------------- #
def login_gate():
    pw = config.get_secret("APP_PASSWORD")
    if not pw:
        return True
    token = _auth_token(str(pw))
    saved = cookie_mgr.get(AUTH_COOKIE)  # 쿠키는 비동기 로드 → 첫 실행엔 None일 수 있음

    logging_out = bool(st.query_params.get("logout")) or st.session_state.get("_logging_out")

    if logging_out:
        # 로그아웃: 쿠키 삭제 명령을 보내고(이 실행에서 플러시) 로그인 폼으로
        st.session_state["_logging_out"] = True
        st.session_state["authed"] = False
        try:
            del st.query_params["logout"]
        except Exception:
            pass
        try:
            cookie_mgr.delete(AUTH_COOKIE)  # 매 실행 멱등 삭제 (재로그인 시 _logging_out 해제됨)
        except Exception:
            pass
    else:
        # 이미 로그인된 세션: 쿠키가 없으면 지금(즉시 rerun 없는 일반 렌더에서) 저장
        if st.session_state.get("authed"):
            if saved != token:
                cookie_mgr.set(AUTH_COOKIE, token,
                               expires_at=dt.datetime.now() + dt.timedelta(days=30))
            return True
        # 쿠키에 유효 토큰이 있으면 자동 로그인
        if saved == token:
            st.session_state["authed"] = True
            return True
        # 쿠키 로드 대기(세션 첫 실행 1회): 로그인된 사용자에게 폼이 깜빡이는 것 방지
        if saved is None and not st.session_state.get("_cookie_checked"):
            st.session_state["_cookie_checked"] = True
            st.markdown("<div class='pagetitle'>🏆 공모전 매니저</div>", unsafe_allow_html=True)
            st.markdown("<div class='subtitle'>불러오는 중…</div>", unsafe_allow_html=True)
            st.stop()

    st.markdown("<div class='pagetitle'>🏆 공모전 매니저</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>로그인이 필요합니다.</div>", unsafe_allow_html=True)
    with st.form("login"):
        entered = st.text_input("비밀번호", type="password")
        ok = st.form_submit_button("로그인", type="primary")
    if ok:
        if entered == pw:
            # 쿠키 저장은 다음 실행(위 authed 경로)에서 — set 직후 rerun하면 쓰기가 취소됨
            st.session_state["authed"] = True
            st.session_state["_logging_out"] = False
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    return False


if not login_gate():
    st.stop()


# --------------------------------------------------------------------------- #
# 헬퍼
# --------------------------------------------------------------------------- #
def parse_dday(dday: str):
    """남은 일수(int) 또는 None. '접수중'/'D-DAY' 등 처리."""
    if not dday:
        return None
    t = dday.replace(" ", "").upper()
    if "DDAY" in t or "TODAY" in t or t == "D-DAY":
        return 0
    m = re.search(r"D-(\d+)", t)
    if m:
        return int(m.group(1))
    return None


def dday_badge(dday: str) -> str:
    d = parse_dday(dday)
    if d is None:
        return f"<span class='badge b-info'>{dday or '-'}</span>"
    if d <= 7:
        return f"<span class='badge b-soon'>D-{d}</span>"
    return f"<span class='badge b-ok'>D-{d}</span>"


def status_badge(status: str) -> str:
    cls = {"준비중": "b-info", "제출완료": "b-ok", "발표대기": "b-gray",
           "수상성공": "b-ok", "아쉬움(탈락)": "b-gray"}.get(status, "b-gray")
    return f"<span class='badge {cls}'>{status}</span>"


# --------------------------------------------------------------------------- #
# 네비게이션 (하단 탭바 — 쿼리파라미터 라우팅)
# --------------------------------------------------------------------------- #
NAV = [("dashboard", "🏠", "홈"), ("explore", "🔍", "탐색"),
       ("projects", "📂", "프로젝트"), ("profile", "👤", "프로필")]
NAV_KEYS = [n[0] for n in NAV]

# (로그아웃은 login_gate 안에서 쿠키 삭제와 함께 처리)
page = st.query_params.get("nav", "dashboard")
if page not in NAV_KEYS:
    page = "dashboard"

# 상단 상태줄
_tc1, _tc2 = st.columns([7, 3])
_logout = " · <a href='?logout=1' target='_self' style='color:#9AA0A6'>로그아웃</a>" if config.get_secret("APP_PASSWORD") else ""
_tc2.markdown(
    f"<div class='topstatus'>저장소: <b>{db.backend}</b> · AI: "
    f"<b>{'연결됨' if config.anthropic_configured() else '미설정'}</b>{_logout}</div>",
    unsafe_allow_html=True,
)


def render_bottom_nav(active):
    html = "<div class='botnav'>"
    for key, ic, lb in NAV:
        cls = "bn-item active" if key == active else "bn-item"
        html += (f"<a class='{cls}' href='?nav={key}' target='_self'>"
                 f"<span class='ic'>{ic}</span><span>{lb}</span></a>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# =========================================================================== #
# 페이지: 대시보드
# =========================================================================== #
def page_dashboard():
    projects = db.list_projects()
    prof = db.get_profile()
    name = (prof.get("name") or "").strip() or "REDUCTO"

    total = len(projects)
    ongoing = sum(1 for p in projects if p.get("status") == "준비중")
    won = sum(1 for p in projects if p.get("status") == "수상성공")
    done = sum(1 for p in projects if p.get("status") in ("제출완료", "발표대기", "수상성공"))

    # 진행/발표대기 중 마감 카운트다운 후보
    upcoming = []
    for p in projects:
        if p.get("status") not in ("준비중", "발표대기"):
            continue
        d = parse_dday((p.get("meta") or {}).get("dday", ""))
        if d is not None:
            upcoming.append((d, p))
    upcoming.sort(key=lambda x: x[0])
    soon = [x for x in upcoming if x[0] <= 7]

    # ---- 인사 헤더 ----
    st.markdown(
        "<div class='apphead'><div class='logo'>🏆</div>"
        "<div><div class='nm'>공모전 매니저</div>"
        "<div class='sm'>나만의 공모전 컨설턴트</div></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='hello'>안녕하세요<b>{name}님 👋</b></div>", unsafe_allow_html=True)
    st.write("")

    # ---- 히어로: 가장 가까운 마감 카운트다운 (클릭 → 해당 프로젝트) ----
    if upcoming:
        d, p = upcoming[0]
        meta = p.get("meta", {})
        big = "D-DAY" if d == 0 else f"D-{d}"
        st.markdown(
            f"<a class='navlink' href='?nav=projects&pid={p['id']}' target='_self'>"
            f"<div class='hero'><div class='pill'>🔥 가장 가까운 마감</div>"
            f"<div class='big'>{big}</div>"
            f"<div class='ttl'>{meta.get('title','')}</div>"
            f"<div class='sub'>{meta.get('category','')} · {meta.get('organizer','')}</div></div></a>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<a class='navlink' href='?nav=explore' target='_self'>"
            "<div class='hero'><div class='pill'>🔥 마감 카운트다운</div>"
            "<div class='big' style='font-size:34px;color:#9AA0A6'>예정된 마감 없음</div>"
            "<div class='sub'>‘공모전 탐색’에서 새 공모전에 참가해보세요.</div></div></a>",
            unsafe_allow_html=True,
        )

    # ---- 통계 타일 (클릭 → 프로젝트 목록) ----
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, cls in [
        (c1, "전체 프로젝트", total, ""), (c2, "진행중", ongoing, "p"),
        (c3, "마감 임박", len(soon), "r"), (c4, "수상", won, "g"),
    ]:
        col.markdown(
            f"<a class='navlink' href='?nav=projects' target='_self'>"
            f"<div class='tile'><div class='label'>{label}</div>"
            f"<div class='value {cls}'>{value}</div></div></a>", unsafe_allow_html=True)
    st.write("")

    left, right = st.columns([1, 1])

    # ---- 현황 진행바 + 분야별 활동 바 ----
    with left:
        pct = int(done / total * 100) if total else 0
        st.markdown(
            f"<div class='card'><div class='sechead'>🎯 진행 현황 "
            f"<span style='float:right;color:#9AA0A6;font-weight:600'>{done} / {total} 완료</span></div>"
            + bar_row("완료율", f"{pct}%", pct, "linear-gradient(90deg,#6C5CE7,#8A7CF8)")
            + "</div>",
            unsafe_allow_html=True,
        )

        # 분야별 프로젝트 분포
        cat_count = {}
        for p in projects:
            c = (p.get("meta") or {}).get("category", "기타") or "기타"
            cat_count[c] = cat_count.get(c, 0) + 1
        palette = ["var(--accent)", "var(--orange)", "var(--pink)", "var(--blue)", "var(--green)"]
        maxv = max(cat_count.values()) if cat_count else 1
        bars = ""
        for i, (c, n) in enumerate(sorted(cat_count.items(), key=lambda x: -x[1])[:5]):
            bars += bar_row(c, f"{n}개", int(n / maxv * 100), palette[i % len(palette)])
        if not bars:
            bars = "<div style='color:#9AA0A6;font-size:13px'>아직 프로젝트가 없어요.</div>"
        st.markdown(f"<div class='card'><div class='sechead'>📊 분야별 프로젝트</div>{bars}</div>",
                    unsafe_allow_html=True)

    # ---- 다가오는 마감 (D-Day 리스트) ----
    with right:
        rows = ""
        dot_colors = {True: "var(--red)", False: "var(--accent)"}
        for d, p in upcoming[:6]:
            meta = p.get("meta", {})
            color = dot_colors[d <= 7]
            rows += (
                f"<a class='rowlink' href='?nav=projects&pid={p['id']}' target='_self'>"
                f"<div class='barrow' style='justify-content:space-between'>"
                f"<div><span class='dot' style='background:{color}'></span>"
                f"<b style='color:var(--ink)'>{meta.get('title','')}</b><br>"
                f"<span style='color:var(--muted);font-size:12px;margin-left:17px'>{meta.get('organizer','')}</span></div>"
                f"<div>{dday_badge(meta.get('dday',''))}</div></div></a>"
            )
        if not rows:
            rows = "<div style='color:#9AA0A6;font-size:13px'>다가오는 마감이 없어요.</div>"
        st.markdown(f"<div class='card'><div class='sechead'>📅 다가오는 마감 (D-Day)</div>{rows}</div>",
                    unsafe_allow_html=True)


# =========================================================================== #
# 페이지: 프로필
# =========================================================================== #
def page_profile():
    st.markdown("<div class='pagetitle'>내 프로필</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>AI 추천과 초안 생성의 기준이 되는 정보예요. 솔직하고 구체적으로 적을수록 좋아요.</div>",
                unsafe_allow_html=True)

    prof = db.get_profile()
    cat_names = list(Scraper.CATEGORY_MAP.values())

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("이름/닉네임", prof.get("name", ""))
        major = c2.text_input("전공 / 소속", prof.get("major", ""))
        interests = st.text_input("관심 분야 (쉼표로 구분)", prof.get("interests", ""),
                                  placeholder="예: 서비스기획, UX, 마케팅, 데이터분석")
        skills = st.text_area("보유 역량 / 사용 가능한 툴", prof.get("skills", ""),
                              placeholder="예: Figma, Python, 영상편집(프리미어), 카피라이팅 ...", height=80)
        awards = st.text_area("수상 / 참가 이력", prof.get("awards", ""),
                              placeholder="예: 2025 OO공모전 우수상, OO 서포터즈 2기 ...", height=80)
        strengths = st.text_area("강점 / 차별점", prof.get("strengths", ""), height=80)
        goal = st.text_input("공모전 목표", prof.get("goal", ""),
                             placeholder="예: 포트폴리오용 수상 1개, 상금, 취업 연계 ...")
        bio = st.text_area("자기소개 (자유)", prof.get("bio", ""), height=100)
        preferred = st.multiselect("선호 카테고리 (탐색 추천에 사용)", cat_names,
                                   default=prof.get("preferred_categories", []))

        saved = st.form_submit_button("💾 프로필 저장", type="primary")

    if saved:
        db.save_profile({
            "name": name, "major": major, "interests": interests,
            "skills": skills, "awards": awards, "strengths": strengths,
            "goal": goal, "bio": bio, "preferred_categories": preferred,
        })
        st.success("프로필을 저장했습니다.")


# =========================================================================== #
# 페이지: 공모전 탐색
# =========================================================================== #
def page_explore():
    st.markdown("<div class='pagetitle'>공모전 탐색</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>위비티에서 크롤링한 공모전을 보고, AI가 내 프로필에 맞는 걸 추천해줘요.</div>",
                unsafe_allow_html=True)

    cat_options = {"전체보기": "all"}
    for code, nm in Scraper.CATEGORY_MAP.items():
        cat_options[nm] = code

    c1, c2, c3 = st.columns([2, 1, 1])
    cat_label = c1.selectbox("분야", list(cat_options.keys()))
    pages = c2.number_input("페이지 수", 1, 20, 3)
    search = c3.button("🔍 검색", type="primary", use_container_width=True)

    if search:
        with st.spinner("공모전 목록을 가져오는 중..."):
            data = scraper.get_contest_list(cat_options[cat_label], int(pages))
        seen = db.get_seen()
        data = [d for d in data if d["id"] not in seen]
        st.session_state["explore_list"] = data
        st.session_state.pop("recs", None)
        st.success(f"새 공모전 {len(data)}건 발견")

    contests = st.session_state.get("explore_list", [])
    if not contests:
        st.info("검색 버튼을 눌러 공모전을 불러오세요.")
        return

    # ---- AI 추천 ----
    ac1, ac2 = st.columns([1, 3])
    if ac1.button("🤖 AI 추천 받기", use_container_width=True,
                  disabled=not config.anthropic_configured()):
        prof = db.get_profile()
        if not prof:
            st.warning("먼저 '프로필'을 입력하면 더 정확하게 추천돼요.")
        history = db.list_projects()  # 여태 참가한 공모전 이력도 함께 반영
        with st.spinner("Claude가 내 프로필과 참가 이력을 분석해 추천 중..."):
            try:
                st.session_state["recs"] = ai.recommend_contests(
                    prof, contests, top_n=5, history=history)
            except Exception as e:
                st.error(f"AI 추천 실패: {e}")
    if not config.anthropic_configured():
        ac2.caption("AI 추천을 쓰려면 ANTHROPIC_API_KEY 설정이 필요해요.")

    recs = st.session_state.get("recs")
    if recs:
        st.markdown("#### 🤖 AI 추천 결과")
        by_id = {c["id"]: c for c in contests}
        for r in recs:
            c = by_id.get(r.get("id"), {})
            cc1, cc2 = st.columns([1, 8])
            cc1.markdown(f"<div class='rec-score'>{r.get('score','')}</div>"
                         f"<div style='color:#868e96;font-size:11px'>적합도</div>",
                         unsafe_allow_html=True)
            tips = f"<br><span style='color:#3b5bdb'>💡 {r.get('tips')}</span>" if r.get("tips") else ""
            cc2.markdown(
                f"<div class='card'><b>{r.get('title','')}</b> "
                f"{dday_badge(c.get('dday',''))}<br>"
                f"<span style='color:#495057'>{r.get('reason','')}</span>{tips}</div>",
                unsafe_allow_html=True,
            )
        st.divider()

    # ---- 목록 테이블 (AI 추천이 맨 위로 + 굵게 강조) ----
    rec_map = {r.get("id"): r for r in (recs or [])}
    # 추천 점수 내림차순 우선, 나머지는 기존 순서 유지(안정 정렬)
    ordered = sorted(contests, key=lambda c: rec_map.get(c["id"], {}).get("score", -1),
                     reverse=True)

    st.markdown("#### 📋 전체 목록")
    st.caption("행을 선택(체크)한 뒤 아래 버튼을 누르세요.  ⭐ = AI 추천 (상단 강조)")

    rows = []
    for c in ordered:
        r = rec_map.get(c["id"])
        rows.append({
            "추천": f"⭐ {r['score']}" if r else "",
            "분야": c["category"], "제목": c["title"],
            "주최": c["organizer"], "D-Day": c["dday"],
        })
    df = pd.DataFrame(rows)

    def _hl(row):
        on = row["추천"] != ""
        s = "font-weight:700;background-color:#f3f1fe;color:#2E2E3A" if on else ""
        return [s] * len(row)

    styler = df.style.apply(_hl, axis=1)
    event = st.dataframe(
        styler, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="multi-row",
        column_config={
            "추천": st.column_config.TextColumn(width="small"),
            "제목": st.column_config.TextColumn(width="large"),
        },
    )
    selected_idx = event.selection.rows if event and event.selection else []

    b1, b2, b3 = st.columns([1, 1, 4])
    if b1.button("➕ 참가하기", type="primary", disabled=not selected_idx):
        added = 0
        for i in selected_idx:
            c = ordered[i]
            ok, _ = db.create_project(c)
            if ok:
                db.add_seen(c["id"]); added += 1
        removed = {ordered[i]["id"] for i in selected_idx}
        st.session_state["explore_list"] = [c for c in contests if c["id"] not in removed]
        st.success(f"{added}개 프로젝트를 생성했습니다.")
        st.rerun()

    if b2.button("🙈 숨기기", disabled=not selected_idx):
        for i in selected_idx:
            db.add_hidden(ordered[i])
        removed = {ordered[i]["id"] for i in selected_idx}
        st.session_state["explore_list"] = [c for c in contests if c["id"] not in removed]
        st.rerun()

    # 숨긴 항목 복구
    with st.expander("🗃 숨긴 공모전 관리 / 복구"):
        hidden = db.get_hidden()
        if not hidden:
            st.caption("숨긴 항목이 없습니다.")
        for h in hidden:
            hc1, hc2 = st.columns([6, 1])
            hc1.write(f"**{h.get('title','')}** · {h.get('organizer','')} · {h.get('dday','')}")
            if hc2.button("복구", key=f"restore_{h.get('id')}"):
                db.remove_hidden(h.get("id"))
                st.rerun()


# =========================================================================== #
# 페이지: 내 프로젝트
# =========================================================================== #
def page_projects():
    st.markdown("<div class='pagetitle'>내 프로젝트</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>참가 중인 공모전을 관리하고 AI로 초안을 만들어요.</div>",
                unsafe_allow_html=True)

    projects = db.list_projects()
    if not projects:
        st.info("아직 프로젝트가 없습니다. '공모전 탐색'에서 참가해보세요.")
        return

    labels = {f"{p['meta'].get('title','(제목없음)')}  ·  {p.get('status','')}": p for p in projects}
    keys = list(labels.keys())

    # 대시보드에서 항목을 클릭해 넘어온 경우(?pid=...) 해당 프로젝트를 선택 상태로
    pid_q = st.query_params.get("pid")
    if pid_q:
        for lbl, pp in labels.items():
            if pp["id"] == pid_q:
                st.session_state["proj_sel"] = lbl
                break
        try:
            del st.query_params["pid"]
        except Exception:
            pass
    # 저장된 선택이 현재 목록에 없으면(삭제 등) 초기화
    if st.session_state.get("proj_sel") not in keys:
        st.session_state.pop("proj_sel", None)

    sel = st.selectbox("프로젝트 선택", keys, key="proj_sel")
    p = labels[sel]
    pid = p["id"]
    meta = p.get("meta", {})

    st.markdown(
        f"<div class='card'><b style='font-size:18px'>{meta.get('title','')}</b> "
        f"{status_badge(p.get('status','준비중'))} {dday_badge(meta.get('dday',''))}<br>"
        f"<span style='color:#868e96'>{meta.get('category','')} · {meta.get('organizer','')}</span><br>"
        f"<a href='{meta.get('link','#')}' target='_blank'>공모전 페이지 열기 ↗</a></div>",
        unsafe_allow_html=True,
    )

    tab_info, tab_files, tab_draft = st.tabs(["📝 상태/일정/메모", "📎 첨부파일", "🤖 AI 초안"])

    # --- 상태/일정/메모 ---
    with tab_info:
        with st.form(f"info_{pid}"):
            statuses = ["준비중", "제출완료", "발표대기", "수상성공", "아쉬움(탈락)"]
            cur = p.get("status", "준비중")
            status = st.selectbox("진행 상태", statuses,
                                  index=statuses.index(cur) if cur in statuses else 0)
            c1, c2 = st.columns(2)
            submit_date = c1.text_input("제출(예정)일", p.get("submit_date", ""), placeholder="2026-06-30")
            announce_date = c2.text_input("발표일", p.get("announce_date", ""), placeholder="2026-07-15")
            prize = st.text_input("상금/혜택 메모", p.get("prize", ""))
            memo = st.text_area("메모", p.get("memo", ""), height=140)
            if st.form_submit_button("💾 저장", type="primary"):
                db.update_project(pid, {
                    "status": status, "submit_date": submit_date,
                    "announce_date": announce_date, "prize": prize, "memo": memo,
                })
                st.success("저장했습니다.")
                st.rerun()

        st.markdown("---")
        dc1, dc2 = st.columns(2)
        if dc1.button("🗑 이 프로젝트 삭제", key=f"del_{pid}", use_container_width=True):
            db.delete_project(pid)
            st.session_state.pop("proj_sel", None)
            st.success("삭제했습니다.")
            st.rerun()
        if dc2.button("🙈 삭제 후 숨기기", key=f"delhide_{pid}", use_container_width=True,
                      help="삭제하고, 탐색 목록에서도 다시 안 뜨도록 숨깁니다."):
            db.add_hidden(meta)          # 탐색에서 다시 안 보이도록(seen에도 등록됨)
            db.delete_project(pid)
            st.session_state.pop("proj_sel", None)
            st.success("삭제하고 숨겼습니다. ‘탐색’에서 다시 보이지 않아요.")
            st.rerun()

    # --- 첨부파일 ---
    with tab_files:
        files = db.list_files(pid)
        for f in files:
            fc1, fc2, fc3 = st.columns([5, 1, 1])
            fc1.write(f"📄 {f['name']}")
            try:
                data = db.get_file(pid, f["name"])
                fc2.download_button("다운로드", data, file_name=f["name"], key=f"dl_{pid}_{f['name']}")
            except Exception:
                fc2.caption("-")
            if fc3.button("삭제", key=f"delf_{pid}_{f['name']}"):
                db.delete_file(pid, f["name"]); st.rerun()
        if not files:
            st.caption("첨부파일이 없습니다.")

        up = st.file_uploader("파일 업로드", accept_multiple_files=True, key=f"up_{pid}")
        if up and st.button("업로드", key=f"upbtn_{pid}"):
            for uf in up:
                db.add_file(pid, uf.name, uf.getvalue())
            st.success(f"{len(up)}개 파일 업로드 완료")
            st.rerun()

    # --- AI 초안 ---
    with tab_draft:
        if not config.anthropic_configured():
            st.warning("AI 초안 생성을 쓰려면 ANTHROPIC_API_KEY 설정이 필요해요.")
        extra = st.text_area("추가 요청 (선택)", key=f"extra_{pid}",
                             placeholder="예: B2C 모바일 앱 위주로, 예산은 적게, 친환경 컨셉 강조 ...")
        use_detail = st.checkbox("공모전 상세 페이지 내용도 참고 (느릴 수 있음)", value=True, key=f"det_{pid}")
        if st.button("✨ 초안 생성", type="primary", key=f"gen_{pid}",
                     disabled=not config.anthropic_configured()):
            prof = db.get_profile()
            detail = ""
            with st.spinner("공모전 정보를 읽고 초안을 작성 중... (최대 1분)"):
                if use_detail and meta.get("link"):
                    detail = scraper.get_contest_detail(meta["link"])
                try:
                    draft = ai.generate_draft(prof, meta, detail, extra)
                    db.update_project(pid, {"draft": draft})
                    st.session_state[f"draft_{pid}"] = draft
                except Exception as e:
                    st.error(f"초안 생성 실패: {e}")

        draft = st.session_state.get(f"draft_{pid}") or p.get("draft", "")
        if draft:
            st.markdown("---")
            st.markdown(draft)
            st.download_button("📥 초안 다운로드 (.md)", draft,
                               file_name=f"{meta.get('title','draft')}_초안.md",
                               key=f"draftdl_{pid}")


# --------------------------------------------------------------------------- #
# 라우팅
# --------------------------------------------------------------------------- #
if page == "dashboard":
    page_dashboard()
elif page == "profile":
    page_profile()
elif page == "explore":
    page_explore()
elif page == "projects":
    page_projects()

render_bottom_nav(page)
