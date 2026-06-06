Set WshShell = CreateObject("WScript.Shell")
' run.bat을 실행하되, 윈도우를 숨김(0) 모드로 실행합니다.
WshShell.Run chr(34) & "run.bat" & Chr(34), 0
Set WshShell = Nothing