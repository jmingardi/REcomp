@echo off
cd /d "%~dp0"
python scripts\project.py run
if errorlevel 1 pause
