@echo off
REM Prefer venv Python if available so the app runs with the project's virtualenv
setlocal
if exist "%~dp0venv\Scripts\python.exe" (
	"%~dp0venv\Scripts\python.exe" "%~dp0generator.py" %*
) else (
	python "%~dp0generator.py" %*
)
endlocal
