@echo off
cd /d %~dp0
start cmd /k "cd /d %~dp0 && type dos_greeting.txt"
