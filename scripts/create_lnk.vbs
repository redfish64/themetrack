Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "shortcut.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\themetrack\scripts\pyinstaller.bat"
oLink.WorkingDirectory = "C:\themetrack\scripts\"
oLink.IconLocation = "C:\themetrack\scripts\themetrack.ico, 0"
oLink.Description = "Themetrack Program"
oLink.Save
