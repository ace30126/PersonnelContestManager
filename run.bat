@echo off
chcp 65001 > nul
cd /d "%~dp0"

:: 가상환경 확인
if not exist venv\Scripts\activate goto ERROR_VENV

:: 가상환경 활성화 및 프로그램 실행 (pythonw 사용, start로 비동기 실행)
call venv\Scripts\activate
start "" "pythonw" main.py
exit

:ERROR_VENV
echo [오류] 'venv' 폴더가 없습니다.
echo 처음 실행하신다면 'setup.bat'을 먼저 실행해서 환경을 설치해주세요.
pause