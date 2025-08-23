@echo off
REM Format code with isort and black (Windows batch)

echo 🔧 Formatting imports with isort...
python -m isort .

echo 🔧 Formatting code with black...
python -m black .

echo ✅ Code formatting complete!