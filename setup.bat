@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo [설치] 공모전 매니저 초기 설정을 시작합니다...
echo.

:: 1. 가상환경 생성
if not exist venv (
    echo 1. 가상환경(venv)을 생성합니다...
    python -m venv venv
) else (
    echo 1. 이미 가상환경이 존재합니다. (건너뜀)
)

:: 2. 라이브러리 설치
echo 2. 필수 라이브러리를 설치합니다...
call venv\Scripts\activate
pip install PyQt6 requests beautifulsoup4 pandas openpyxl google-generativeai

echo.
echo [완료] 모든 설정이 끝났습니다!
echo 이제 'start_quiet.vbs'를 실행하여 프로그램을 시작하세요.
pause