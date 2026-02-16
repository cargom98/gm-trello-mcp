#!/bin/bash
# Quick release script for patch versions
# Usage: ./quick-release.sh "Bug fix description"

set -e

if [ -z "$1" ]; then
    echo "Usage: ./quick-release.sh \"Release description\""
    echo "Example: ./quick-release.sh \"Fix authentication timeout issue\""
    exit 1
fi

DESCRIPTION="$1"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Quick Patch Release${NC}"
echo ""

# Get current version and increment patch
current_version=$(grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
IFS='.' read -r -a parts <<< "$current_version"
major="${parts[0]}"
minor="${parts[1]}"
patch="${parts[2]}"
patch=$((patch + 1))
new_version="$major.$minor.$patch"

echo "Version: $current_version → $new_version"
echo "Description: $DESCRIPTION"
echo ""

# Update version
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
else
    sed -i "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
fi

# Update changelog
date=$(date +%Y-%m-%d)
temp_file=$(mktemp)
echo -e "## [$new_version] - $date\n" > "$temp_file"
echo -e "### Fixed" >> "$temp_file"
echo -e "- $DESCRIPTION\n" >> "$temp_file"
cat CHANGELOG.md >> "$temp_file"
mv "$temp_file" CHANGELOG.md

# Clean and build
rm -rf dist/ build/ *.egg-info
python -m build

# Commit and tag
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release version $new_version

$DESCRIPTION"
git tag -a "v$new_version" -m "Release version $new_version"

echo -e "${GREEN}✓${NC} Release $new_version ready"
echo ""
echo "Next steps:"
echo "  1. Review changes: git show HEAD"
echo "  2. Upload to PyPI: python -m twine upload dist/*"
echo "  3. Push to remote: git push && git push --tags"
echo ""
