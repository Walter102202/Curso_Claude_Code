#!/bin/bash
# Run all code quality checks

echo "🚀 Running code quality checks..."

echo "🔧 Step 1: Formatting code..."
./scripts/format.sh

echo "🔍 Step 2: Running linting..."
./scripts/lint.sh

echo "✅ All quality checks complete!"