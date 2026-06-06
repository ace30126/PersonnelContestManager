# 공모전 매니저 (웹) — 실행 & 배포 가이드

위비티 공모전을 크롤링하고, 내 프로필을 바탕으로 **Claude AI가 적합한 공모전을 추천**하고
**제출 초안까지 자동 생성**해주는 개인용 웹 서비스입니다.

- 프레임워크: Streamlit
- AI: Claude (Anthropic)
- 저장소: Supabase (미설정 시 로컬 JSON 파일로 자동 동작)

---

## 1. 로컬에서 바로 실행하기 (가장 빠름)

```powershell
cd C:\Users\yoons\Desktop\260606_MCM\MyContestManager
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 이 열립니다.

- **API 키/Supabase 없이도** 실행됩니다. (데이터는 `user_data/` 폴더에 JSON으로 저장, AI 버튼은 비활성화)
- AI 기능을 켜려면 키를 넣어야 합니다 ↓

### 로컬에서 AI 켜기
`.streamlit/secrets.toml` 파일을 만들고 (`secrets.toml.example` 복사) 채웁니다:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
# APP_PASSWORD, SUPABASE_* 는 로컬에선 생략 가능
```

> Anthropic 키 발급: https://console.anthropic.com → API Keys

---

## 2. Supabase 영구 저장 연결 (클라우드 배포 전 필수)

클라우드(Streamlit Cloud)는 재시작하면 로컬 파일이 사라지므로 Supabase에 저장합니다.

1. https://supabase.com → 새 프로젝트 생성 (무료)
2. **SQL Editor** 에 `supabase_schema.sql` 내용을 붙여넣고 실행 → 테이블/버킷 생성
3. **Project Settings → API** 에서 값 복사
   - `Project URL` → `SUPABASE_URL`
   - `service_role` key → `SUPABASE_KEY`  *(혼자 쓰는 서비스라 가장 간단. 외부 노출 금지)*
4. `secrets.toml` (또는 Streamlit Cloud Secrets)에 추가:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

연결되면 앱 사이드바에 `저장소: supabase` 로 표시됩니다. (안 되면 `local`)

---

## 3. 외부 접속 — Streamlit Community Cloud 배포 (무료)

1. 이 폴더를 **GitHub 비공개 저장소**로 푸시
   - `.gitignore` 가 `secrets.toml` 과 `user_data/` 를 자동 제외합니다. (키 유출 방지)
2. https://share.streamlit.io → **New app** → 저장소/브랜치/`app.py` 선택
3. **Advanced settings → Secrets** 에 아래를 붙여넣기:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
APP_PASSWORD = "내가정한_로그인_비밀번호"
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

4. Deploy → 발급된 URL로 폰/외부에서 접속. 첫 화면에서 `APP_PASSWORD` 로 로그인.

> `APP_PASSWORD` 를 설정하면 로그인 화면이 생깁니다(외부 배포 시 필수).
> 로컬에서 비워두면 로그인 없이 바로 들어갑니다.

---

## 폴더 구조

```
app.py                  Streamlit 메인 (대시보드/프로필/탐색/프로젝트)
core/
  scraper.py            위비티 크롤러 (+ 상세내용 추출)
  ai.py                 Claude 추천 / 초안 생성
  storage.py            Supabase + 로컬 JSON 저장소
  config.py             secrets/환경변수 로딩
supabase_schema.sql     Supabase 테이블/버킷 생성 SQL
.streamlit/
  config.toml           테마
  secrets.toml          (직접 생성, git 제외) 키 보관
user_data/              로컬 저장 데이터 (git 제외)
```

기존 PyQt6 데스크톱 버전(`main.py`, `ui/`)은 그대로 남아 있으며 웹 버전과 무관합니다.
