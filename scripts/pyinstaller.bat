#pyinstaller.exe themetrack.py  --add-data theme_track_config.xlsx:. --add-data system_rules.xlsx:. --add-data dos_scripts/dos_greeting.txt:. --add-data dos_scripts/themetrack.bat:. --add-data dos_scripts/tt.bat:.
cd /d %~dp0
cd ..
pyinstaller.exe --onefile --name _themetrack themetrack.py
copy theme_track_config.xlsx dist\ 
copy system_rules.xlsx dist\
copy dos_scripts\*.* dist\

