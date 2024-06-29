@echo off

REM changes the behavior of themetrack.py to not open welcome.bat
set IN_WELCOME_BAT=1

start cmd /k "cd /d %~dp0 && type dos_greeting.txt"
