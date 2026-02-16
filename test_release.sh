#!/bin/bash
# Test script to verify release scripts are working

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Testing release scripts..."
echo ""

# Test 1: Check if scripts exist
echo -n "Checking if release.sh exists... "
if [ -f "release.sh" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

echo -n "Checking if quick-release.sh exists... "
if [ -f "quick-release.sh" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test 2: Check if scripts are executable
echo -n "Checking if release.sh is executable... "
if [ -x "release.sh" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (run: chmod +x release.sh)"
fi

echo -n "Checking if quick-release.sh is executable... "
if [ -x "quick-release.sh" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (run: chmod +x quick-release.sh)"
fi

# Test 3: Check if required tools are installed
echo -n "Checking if python is installed... "
if command -v python &> /dev/null; then
    echo -e "${GREEN}✓${NC} ($(python --version))"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

echo -n "Checking if build module is installed... "
if python -c "import build" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (run: pip install build)"
fi

echo -n "Checking if twine is installed... "
if python -c "import twine" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} (run: pip install twine)"
fi

# Test 4: Check if pyproject.toml has version
echo -n "Checking pyproject.toml version... "
version=$(grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/' || echo "")
if [ -n "$version" ]; then
    echo -e "${GREEN}✓${NC} (current: $version)"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test 5: Check if CHANGELOG.md exists
echo -n "Checking if CHANGELOG.md exists... "
if [ -f "CHANGELOG.md" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Test 6: Check git status
echo -n "Checking git repository... "
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All checks passed!${NC}"
echo ""
echo "You can now use:"
echo "  ./release.sh              - Interactive release"
echo "  ./quick-release.sh \"msg\"  - Quick patch release"
echo ""
