import os
import sys
import win32com.client

def create_shortcut(target, shortcut_path, icon_path, description=""):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    shortcut.IconLocation = icon_path
    shortcut.Description = description
    shortcut.save()

if __name__ == "__main__":
    target = r"C:\themetrack\scripts\pyinstaller.bat"  # The batch file you want to create a shortcut for
    shortcut_path = r"C:\themetrack\scripts\shortcut.lnk"  # Where you want the shortcut to be created
    icon_path = r"C:\themetrack\scripts\themetrack.ico"  # The icon file

    # Ensure paths are correctly formatted
    target = os.path.abspath(target)
    shortcut_path = os.path.abspath(shortcut_path)
    icon_path = os.path.abspath(icon_path)

    create_shortcut(target, shortcut_path, icon_path, "Themetrack Program")
    print(f"Shortcut created at {shortcut_path}")

