#!/bin/bash
# Check or fix code formatting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to check mode
MODE="check"

# Parse arguments
if [[ "$1" == "fix" ]]; then
    MODE="fix"
fi

echo "🔍 Running code quality checks..."
echo ""

if [[ "$MODE" == "check" ]]; then
    echo "Mode: CHECK (use './scripts/lint.sh fix' to auto-fix issues)"
    echo "============================================"

    # Check black formatting
    echo -e "\n📏 Checking code formatting with black..."
    if poetry run black --check --diff snapshotter_cli/ tests/ *.py 2>/dev/null; then
        echo -e "${GREEN}✅ Black check passed${NC}"
    else
        echo -e "${RED}❌ Black check failed${NC}"
        echo -e "${YELLOW}Run './scripts/lint.sh fix' to auto-format${NC}"
        exit 1
    fi

    # Check isort
    echo -e "\n📦 Checking import sorting with isort..."
    if poetry run isort --check-only --diff snapshotter_cli/ tests/ *.py 2>/dev/null; then
        echo -e "${GREEN}✅ Isort check passed${NC}"
    else
        echo -e "${RED}❌ Isort check failed${NC}"
        echo -e "${YELLOW}Run './scripts/lint.sh fix' to auto-sort imports${NC}"
        exit 1
    fi

    # Run pre-commit on all files
    echo -e "\n🔧 Running all pre-commit hooks..."
    if poetry run pre-commit run --all-files; then
        echo -e "\n${GREEN}✅ All checks passed!${NC}"
    else
        echo -e "\n${RED}❌ Some checks failed${NC}"
        echo -e "${YELLOW}Run './scripts/lint.sh fix' to auto-fix formatting issues${NC}"
        exit 1
    fi

else
    echo "Mode: FIX (auto-fixing issues)"
    echo "================================"

    # Fix with isort
    echo -e "\n📦 Fixing import sorting with isort..."
    poetry run isort snapshotter_cli/ tests/ *.py 2>/dev/null || true
    echo -e "${GREEN}✅ Isort formatting applied${NC}"

    # Fix with black
    echo -e "\n📏 Fixing code formatting with black..."
    poetry run black snapshotter_cli/ tests/ *.py 2>/dev/null || true
    echo -e "${GREEN}✅ Black formatting applied${NC}"

    # Check if all issues are fixed
    echo -e "\n🔍 Verifying all fixes..."
    if poetry run pre-commit run --all-files; then
        echo -e "\n${GREEN}✅ All formatting issues fixed!${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Some issues may require manual attention${NC}"
        echo "Check the output above for details."
        exit 1
    fi
fi
