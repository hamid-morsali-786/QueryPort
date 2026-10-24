@echo off
echo ===================================================
echo   Building QueryPort Standalone Executable
echo ===================================================

pyinstaller --noconfirm --clean ^
  --onefile ^
  --name "QueryPort" ^
  --collect-all oracledb ^
  --collect-all cryptography ^
  --hidden-import import_sql ^
  export_sql.py

echo.
echo Build completed! Executable is located in dist\QueryPort.exe
pause
