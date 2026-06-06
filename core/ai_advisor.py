import google.generativeai as genai
import os

# API 키 설정 (환경 변수 혹은 직접 입력)
# genai.configure(api_key="YOUR_API_KEY")

def get_recommendation(my_history_json, new_contests_list):
    """
    Gemini에게 내py 활동 내역을 기반으로 새 공모전을 추천받음
    """
    
    # 1. 프롬프트 구성
    prompt = f"""
    당신은 전문 공모전 컨설턴트입니다. 
    
    [나의 공모전 참가 이력]
    {my_history_json}
    
    [새로 발견된 공모전 목록]
    {new_contests_list}
    
    [요청사항]
    위의 '나의 참가 이력'을 분석하여 성향을 파악한 뒤, 
    '새로 발견된 공모전 목록' 중에서 나에게 가장 적합한 공모전 TOP 3를 추천해주세요.
    추천 이유를 구체적으로 설명해주세요.
    결과는 읽기 편한 텍스트 형식으로 주세요.
    """

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {e}"