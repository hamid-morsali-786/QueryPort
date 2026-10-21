@echo off
echo ===================================================
echo   Building QueryPort Standalone Executable
echo ===================================================

pyinstaller --noconfirm --clean ^
  --onedir=false --onefile ^
  --name "QueryPort" ^
  --add-data "config.json;." ^
  export_sql.py

echo.
echo Build completed! Executable is located in dist\QueryPort.exe
pause
