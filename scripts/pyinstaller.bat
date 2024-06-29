cd /d %~dp0
cd ..
pyinstaller.exe --name themetrack --icon=images\themetrack.ico themetrack.py ^
--add-data system_rules.xlsx:. ^
--add-data theme_track_config.xlsx:. ^
--add-data dos_scripts/welcome.bat:dos_scripts

mkdir dist\themetrack\dos_scripts
copy dos_scripts\dos_greeting.txt dist\themetrack\dos_scripts\
