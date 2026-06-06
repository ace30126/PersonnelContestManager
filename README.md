# 🏆 공모전 매니저 (웹)

위비티 공모전을 크롤링하고, 내 프로필을 바탕으로 **Claude AI가 적합한 공모전을 추천**하고
**제출 초안까지 자동 생성**해주는 개인용 웹 서비스.

- **프레임워크**: Streamlit
- **AI**: Claude (Anthropic)
- **저장소**: Supabase (미설정 시 로컬 JSON 자동 폴백)

## 빠른 실행 (로컬)

```bash
pip install -r requirements.txt
streamlit run app.py
```

`http://localhost:8501` 접속. API 키 없이도 동작하며, AI를 켜려면
`.streamlit/secrets.toml` 에 `ANTHROPIC_API_KEY` 를 넣습니다.

## 배포 / Supabase 연결

[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) 참고.

## 기능
- 📊 대시보드 — 마감 카운트다운, 진행 현황, 분야별 분포, 다가오는 마감
- 👤 프로필 — AI 추천/초안의 기준 정보
- 🔍 공모전 탐색 — 크롤링 + AI 적합도 추천(상단 강조)
- 📂 내 프로젝트 — 상태/일정/메모/첨부파일 + AI 제출 초안 생성
