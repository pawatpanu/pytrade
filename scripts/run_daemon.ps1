$ErrorActionPreference = "Stop"
Set-Location "C:\pytrade"
New-Item -ItemType Directory -Force -Path "C:\pytrade\logs" | Out-Null
& "C:\pytrade\.venv\Scripts\python.exe" main.py --mode daemon *>> "C:\pytrade\logs\daemon.log"
