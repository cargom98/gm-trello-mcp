#!/bin/bash
# Quick release script for patch versions
# Usage: ./quick-release.sh [optional description]

set -e

DESCRIPTION="$1"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# Get commits since last tag
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$last_tag" ]; then
    commits=$(git log --pretty=format:"%s" --no-merges)
else
    commits=$(git log "${last_tag}..HEAD" --pretty=format:"%s" --no-merges)
fi

# If description provided, use it; otherwise generate from commits
if [ -n "$DESCRIPTION" ]; then
    echo "Description: $DESCRIPTION"
    changelog_content="- $DESCRIPTION"
else
    echo -e "${YELLOW}Generating changelog from commits...${NC}"
    changelog_content=""
    while IFS= read -r commit; do
        [ -z "$commit" ] && continue
        # Extract message from conventional commits or use as-is
        if [[ $commit =~ ^(feat|fix|refactor|perf|style|docs|chore)(\(.*\))?:\ (.+) ]]; then
            changelog_content="${changelog_content}- ${BASH_REMATCH[3]}\n"
        else
            changelog_content="${changelog_content}- ${commit}\n"
        fi
    done <<< "$commits"
    
    if [ -z "$changelog_content" ]; then
        changelog_content="- Patch release"
    fi
    
    echo -e "\nChangelog entries:"
    echo -e "$changelog_content"
fi

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
echo -e "$changelog_content" >> "$temp_file"
echo "" >> "$temp_file"
cat CHANGELOG.md >> "$temp_file"
mv "$temp_file" CHANGELOG.md

# Clean and build
rm -rf dist/ build/ *.egg-info
python -m build

# Commit and tag
git add pyproject.toml CHANGELOG.md
if [ -n "$DESCRIPTION" ]; then
    git commit -m "chore: release version $new_version

$DESCRIPTION"
else
    git commit -m "chore: release version $new_version"
fi
git tag -a "v$new_version" -m "Release version $new_version"

echo -e "${GREEN}✓${NC} Release $new_version ready"
echo ""
echo "Next steps:"
echo "  1. Review changes: git show HEAD"
echo "  2. Upload to PyPI: python -m twine upload dist/*"
echo "  3. Push to remote: git push && git push --tags"
echo ""
