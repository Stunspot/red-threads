@echo off
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 "%~dp0work-host.py" %*
) else (
  python "%~dp0work-host.py" %*
)
if errorlevel 1 pause
