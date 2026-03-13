$ErrorActionPreference = "Stop"
Set-Location "C:\pytrade"
New-Item -ItemType Directory -Force -Path "C:\pytrade\logs" | Out-Null
& "C:\pytrade\.venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1 *>> "C:\pytrade\logs\dashboard.log"
