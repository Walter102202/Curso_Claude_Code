#!/bin/bash
# Format code with isort and black

echo "🔧 Formatting imports with isort..."
python -m isort .

echo "🔧 Formatting code with black..."
python -m black .

echo "✅ Code formatting complete!"