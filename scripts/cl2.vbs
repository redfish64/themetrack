Set oWS = WScript.CreateObject("WScript.Shell")
Set oFSO = CreateObject("Scripting.FileSystemObject")

' Get the path of the current script
currentDir = oFSO.GetParentFolderName(WScript.ScriptFullName)

' Define relative paths
shortcutName = "shortcut.lnk"
targetPath = "your_script.bat"
iconPath = "your_icon.ico"

' Combine the current directory with the relative paths
sLinkFile = oFSO.BuildPath(currentDir, shortcutName)
targetFullPath = oFSO.BuildPath(currentDir, targetPath)
iconFullPath = oFSO.BuildPath(currentDir, iconPath)

' Create the shortcut
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = targetFullPath
oLink.WorkingDirectory = currentDir
oLink.IconLocation = iconFullPath
oLink.Description = "Themetrack Program"
oLink.Save

WScript.Echo "Shortcut created at " & sLinkFile
