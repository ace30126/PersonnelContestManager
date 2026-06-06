"""
Claude(Anthropic) 기반 AI 기능.

- recommend_contests : 내 프로필 + 크롤링한 공모전 목록 -> 적합도 추천(구조화 JSON)
- generate_draft     : 내 프로필 + 공모전 정보(+상세) -> 기획서/제출안 초안 생성

프롬프트 캐싱(cache_control)을 사용해 시스템 프롬프트/프로필 재사용 비용을 줄인다.
"""
import json

import anthropic

from core import config


def _client():
    key = config.get_secret("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    return anthropic.Anthropic(api_key=key)


def _profile_text(profile: dict) -> str:
    if not profile:
        return "(프로필 정보 없음)"
    lines = []
    label = {
        "name": "이름", "major": "전공/소속", "interests": "관심 분야",
        "skills": "보유 역량/툴", "awards": "수상/참가 이력",
        "strengths": "강점/차별점", "bio": "자기소개", "goal": "공모전 목표",
        "preferred_categories": "선호 카테고리",
    }
    for k, v in profile.items():
        if not v:
            continue
        if isinstance(v, list):
            v = ", ".join(map(str, v))
        lines.append(f"- {label.get(k, k)}: {v}")
    return "\n".join(lines) if lines else "(프로필 정보 없음)"


# --------------------------------------------------------------------------- #
# 1) 공모전 추천
# --------------------------------------------------------------------------- #
RECOMMEND_TOOL = {
    "name": "recommend",
    "description": "사용자에게 가장 적합한 공모전을 적합도 순으로 추천한다.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "공모전 목록의 id 값 그대로"},
                        "title": {"type": "string"},
                        "score": {"type": "integer", "description": "적합도 0~100"},
                        "reason": {"type": "string", "description": "추천 이유(구체적으로, 2~3문장)"},
                        "tips": {"type": "string", "description": "이 공모전을 준비할 때의 한 줄 전략"},
                    },
                    "required": ["id", "title", "score", "reason"],
                },
            }
        },
        "required": ["recommendations"],
    },
}


def recommend_contests(profile: dict, contests: list, top_n: int = 5) -> list:
    """contests: [{id,title,category,organizer,dday,link}, ...]
    반환: [{id,title,score,reason,tips}, ...] (적합도 내림차순)"""
    if not contests:
        return []

    client = _client()
    # 토큰 절약: 추천 판단에 필요한 필드만 추림
    slim = [
        {"id": c.get("id"), "title": c.get("title"),
         "category": c.get("category"), "organizer": c.get("organizer"),
         "dday": c.get("dday")}
        for c in contests
    ]

    system = [{
        "type": "text",
        "text": (
            "당신은 공모전/대외활동 전문 컨설턴트입니다. 사용자의 프로필(전공, 역량, "
            "이력, 관심사)을 분석해 성향을 파악하고, 주어진 공모전 목록 중 가장 적합한 "
            "것을 골라 적합도 점수와 구체적 근거를 제시합니다. 반드시 recommend 도구로만 "
            "답하세요. id는 목록의 값을 그대로 사용합니다."
        ),
        "cache_control": {"type": "ephemeral"},
    }]

    user = (
        f"[내 프로필]\n{_profile_text(profile)}\n\n"
        f"[새로 발견된 공모전 목록(JSON)]\n{json.dumps(slim, ensure_ascii=False)}\n\n"
        f"위 목록에서 나에게 가장 적합한 공모전 TOP {top_n}을 골라 추천해줘."
    )

    resp = client.messages.create(
        model=config.recommend_model(),
        max_tokens=2000,
        system=system,
        tools=[RECOMMEND_TOOL],
        tool_choice={"type": "tool", "name": "recommend"},
        messages=[{"role": "user", "content": user}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "recommend":
            recs = block.input.get("recommendations", [])
            recs.sort(key=lambda r: r.get("score", 0), reverse=True)
            return recs[:top_n]
    return []


# --------------------------------------------------------------------------- #
# 2) 초안 생성
# --------------------------------------------------------------------------- #
def generate_draft(profile: dict, contest_meta: dict, detail: str = "",
                   extra_instructions: str = "") -> str:
    """공모전 제출용 기획서/아이디어 초안을 마크다운으로 생성."""
    client = _client()

    system = [{
        "type": "text",
        "text": (
            "당신은 수상 경력이 풍부한 공모전 멘토이자 기획서 작성 전문가입니다. "
            "사용자의 프로필과 공모전 정보를 바탕으로, 실제 제출 가능한 수준의 구체적이고 "
            "설득력 있는 초안을 한국어 마크다운으로 작성합니다. 추상적 미사여구 대신 "
            "심사 기준을 의식한 구조와 실행 가능한 아이디어를 제시하세요."
        ),
        "cache_control": {"type": "ephemeral"},
    }]

    detail_block = f"\n\n[공모전 상세 내용]\n{detail.strip()}" if detail.strip() else ""
    extra_block = f"\n\n[추가 요청사항]\n{extra_instructions.strip()}" if extra_instructions.strip() else ""

    user = (
        f"[내 프로필]\n{_profile_text(profile)}\n\n"
        f"[공모전 정보]\n"
        f"- 제목: {contest_meta.get('title','')}\n"
        f"- 주최: {contest_meta.get('organizer','')}\n"
        f"- 분야: {contest_meta.get('category','')}\n"
        f"- 마감: {contest_meta.get('dday','')}\n"
        f"- 링크: {contest_meta.get('link','')}"
        f"{detail_block}{extra_block}\n\n"
        "위 정보를 바탕으로 이 공모전 제출용 초안을 작성해줘. 다음 구조를 포함해:\n"
        "1. 추천 출품 주제(2~3안)와 각 컨셉 한 줄 요약\n"
        "2. 가장 추천하는 주제를 골라 작성한 본 기획안\n"
        "   - 배경/문제정의, 핵심 아이디어, 타깃, 차별점, 기대효과, 실행/구현 방안\n"
        "3. 내 프로필 강점을 어떻게 어필할지\n"
        "4. 심사위원이 좋아할 포인트 / 주의할 점 체크리스트\n"
        "내 프로필의 전공·역량과 자연스럽게 연결해줘."
    )

    resp = client.messages.create(
        model=config.draft_model(),
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")
