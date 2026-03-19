' This script launches the Python service without opening a visible command prompt window.
Set WshShell = CreateObject("WScript.Shell")
' Run pythonw.exe (which runs python without a console) 
' The 0 means hide window, False means don't wait for it to finish.
WshShell.Run "pythonw.exe -m pyworkspace.service", 0, False
