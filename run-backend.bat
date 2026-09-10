@echo off
echo ========================================================
echo Starting NexPharmAI FastAPI Backend Server (Port 8000)...
echo ========================================================
cd /d "%~dp0backend"

if exist "venv\Scripts\uvicorn.exe" (
    echo Using backend virtual environment...
    .\venv\Scripts\uvicorn app.main:app --port 8000 --reload
) else (
    echo Using system Python uvicorn...
    uvicorn app.main:app --port 8000 --reload
)
