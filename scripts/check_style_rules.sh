#!/usr/bin/env bash
# check_style_rules.sh — Enforce KIR STYLE_GUIDE.md rules

set -e

ERRORS=0

echo "Checking KIR Python Style Guide rules..."
echo ""

# Rule 1: No TYPE_CHECKING blocks
echo "1. Checking for TYPE_CHECKING blocks (should be none)..."
if grep -r "if TYPE_CHECKING:" src/kir --include="*.py" > /dev/null 2>&1; then
    echo "❌ FAIL: Found 'if TYPE_CHECKING:' blocks (forbidden by STYLE_GUIDE.md)"
    grep -r "if TYPE_CHECKING:" src/kir --include="*.py" | sed 's/^/   /'
    ERRORS=$((ERRORS + 1))
else
    echo "✓ PASS: No TYPE_CHECKING blocks found"
fi
echo ""

# Rule 2: No __future__ annotations
echo "2. Checking for __future__ annotations imports (should be none)..."
if grep -r "from __future__ import annotations" src/kir --include="*.py" > /dev/null 2>&1; then
    echo "❌ FAIL: Found '__future__ annotations' imports (forbidden by STYLE_GUIDE.md)"
    grep -r "from __future__ import annotations" src/kir --include="*.py" | sed 's/^/   /'
    ERRORS=$((ERRORS + 1))
else
    echo "✓ PASS: No __future__ annotations found"
fi
echo ""

# Exit with error if any rules violated
if [ $ERRORS -gt 0 ]; then
    echo "❌ Style check failed with $ERRORS violations"
    exit 1
else
    echo "✅ All style rules passed!"
    exit 0
fi
