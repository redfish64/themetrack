Create_ShortCut "C:\WINDOWS\NOTEPAD.EXE", "Desktop", "Notepad", "test arg", , WshNormalFocus
 
Private Sub Create_ShortCut(ByVal sTargetPath As String, ByVal sShortCutPath As String, ByVal sShortCutName As String, _
                            Optional ByVal sArguments As String, Optional ByVal sWorkPath As String, _
                            Optional ByVal eWinStyle As WshWindowStyle = vbNormalFocus, Optional ByVal iIconNum As Integer)
    ' Requires reference to Windows Script Host Object Model
    Dim oShell As IWshRuntimeLibrary.WshShell
    Dim oShortCut As IWshRuntimeLibrary.WshShortcut
    
    Set oShell = New IWshRuntimeLibrary.WshShell
    Set oShortCut = oShell.CreateShortcut(oShell.SpecialFolders(sShortCutPath) & _
                                          "\" & sShortCutName & ".lnk")
    With oShortCut
        .TargetPath = sTargetPath
        .Arguments = sArguments
        .WorkingDirectory = sWorkPath
        .WindowStyle = eWinStyle
        .IconLocation = sTargetPath & "," & iIconNum
        .Save
    End With
    
    Set oShortCut = Nothing: Set oShell = Nothing
End Sub