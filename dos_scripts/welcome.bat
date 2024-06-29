@echo off

REM changes the behavior of themetrack.py to not open welcome.bat
set IN_WELCOME_BAT=1

start cmd /k "type dos_scripts\dos_greeting.txt"
