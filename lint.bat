@echo off
REM Run code quality checks (Windows batch)

echo 🔍 Running flake8 linting...
python -m flake8 .

if %errorlevel% equ 0 (
    echo ✅ Linting passed!
) else (
    echo ❌ Linting failed. Please fix the issues above.
    exit /b 1
)