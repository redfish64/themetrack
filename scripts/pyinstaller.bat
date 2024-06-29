pyinstaller.exe themetrack.py --onefile  --add-data theme_track_config.xlsx:. ^
--add-data system_rules.xlsx:. ^
--add-data dos_scripts/dos_greeting.txt:dos_scripts ^
--add-data dos_scripts/welcome.bat:dos_scripts

