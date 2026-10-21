@echo off
echo ===================================================
echo   Building QueryPort Standalone Executable
echo ===================================================

pyinstaller --noconfirm --clean ^
  --onefile ^
  --name "QueryPort" ^
  --collect-all oracledb ^
  --collect-all cryptography ^
  --add-data "config.json;." ^
  export_sql.py

echo.
echo Build completed! Executable is located in dist\QueryPort.exe
pause
