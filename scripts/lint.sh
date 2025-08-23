#!/bin/bash
# Run code quality checks

echo "🔍 Running flake8 linting..."
python -m flake8 .

if [ $? -eq 0 ]; then
    echo "✅ Linting passed!"
else
    echo "❌ Linting failed. Please fix the issues above."
    exit 1
fi