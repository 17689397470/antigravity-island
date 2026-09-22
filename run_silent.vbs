Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "pythonw " & Chr(34) & currentDir & "\capsule_gui.py" & Chr(34)
WshShell.Run cmd, 0, False
Set WshShell = Nothing
Set fso = Nothing
