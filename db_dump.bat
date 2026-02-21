@echo off
chcp 65001 >nul
set PGPASSWORD=knou1234
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U knou_user -d knou_agriculture -F c -f db_backup.dump
if %errorlevel% equ 0 (
    echo [OK] db_backup.dump saved successfully!
) else (
    echo [FAIL] pg_dump failed with error code %errorlevel%
)
set PGPASSWORD=
pause
