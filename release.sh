#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to get current version from pyproject.toml
get_current_version() {
    grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Function to update version in pyproject.toml
update_version() {
    local new_version=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
    else
        # Linux
        sed -i "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
    fi
}

# Function to increment version
increment_version() {
    local version=$1
    local part=$2
    
    IFS='.' read -r -a parts <<< "$version"
    major="${parts[0]}"
    minor="${parts[1]}"
    patch="${parts[2]}"
    
    case $part in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            print_error "Invalid version part: $part"
            exit 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Function to get commits since last tag
get_commits_since_last_tag() {
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$last_tag" ]; then
        # No tags yet, get all commits
        git log --pretty=format:"%s" --no-merges
    else
        # Get commits since last tag
        git log "${last_tag}..HEAD" --pretty=format:"%s" --no-merges
    fi
}

# Function to categorize commits
categorize_commits() {
    local commits="$1"
    local added=""
    local changed=""
    local fixed=""
    local other=""
    
    while IFS= read -r commit; do
        # Skip empty lines
        [ -z "$commit" ] && continue
        
        # Categorize by conventional commit prefix
        if [[ $commit =~ ^feat(\(.*\))?:\ (.+) ]]; then
            added="${added}- ${BASH_REMATCH[2]}\n"
        elif [[ $commit =~ ^fix(\(.*\))?:\ (.+) ]]; then
            fixed="${fixed}- ${BASH_REMATCH[2]}\n"
        elif [[ $commit =~ ^(refactor|perf|style|docs|chore)(\(.*\))?:\ (.+) ]]; then
            changed="${changed}- ${BASH_REMATCH[3]}\n"
        else
            # Non-conventional commits go to Changed
            other="${other}- ${commit}\n"
        fi
    done <<< "$commits"
    
    # Combine changed and other
    changed="${changed}${other}"
    
    echo -e "ADDED:${added}CHANGED:${changed}FIXED:${fixed}"
}

# Function to add changelog entry
add_changelog_entry() {
    local version=$1
    local date=$(date +%Y-%m-%d)
    local temp_file=$(mktemp)
    
    # Get commits since last tag
    print_info "Gathering commits since last release..."
    local commits=$(get_commits_since_last_tag)
    
    if [ -z "$commits" ]; then
        print_warning "No commits found since last release"
        commits="- Initial release"
    fi
    
    # Categorize commits
    local categorized=$(categorize_commits "$commits")
    local added=$(echo "$categorized" | grep -A 1000 "ADDED:" | grep -B 1000 "CHANGED:" | grep -v "ADDED:" | grep -v "CHANGED:")
    local changed=$(echo "$categorized" | grep -A 1000 "CHANGED:" | grep -B 1000 "FIXED:" | grep -v "CHANGED:" | grep -v "FIXED:")
    local fixed=$(echo "$categorized" | grep -A 1000 "FIXED:" | grep -v "FIXED:")
    
    # Create new entry
    echo -e "## [$version] - $date\n" > "$temp_file"
    
    if [ -n "$added" ]; then
        echo -e "### Added" >> "$temp_file"
        echo -e "$added" >> "$temp_file"
    fi
    
    if [ -n "$changed" ]; then
        echo -e "### Changed" >> "$temp_file"
        echo -e "$changed" >> "$temp_file"
    fi
    
    if [ -n "$fixed" ]; then
        echo -e "### Fixed" >> "$temp_file"
        echo -e "$fixed" >> "$temp_file"
    fi
    
    echo "" >> "$temp_file"
    
    # Append existing changelog
    cat CHANGELOG.md >> "$temp_file"
    mv "$temp_file" CHANGELOG.md
    
    print_success "Changelog generated from commits"
    print_info "Review and edit CHANGELOG.md if needed"
}

# Main script
echo ""
print_info "═══════════════════════════════════════════════════════════"
print_info "  Trello MCP Server - Release Script"
print_info "═══════════════════════════════════════════════════════════"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    print_error "You have uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

# Check if on main/master branch
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
    print_warning "You are on branch '$current_branch', not 'main' or 'master'"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get current version
current_version=$(get_current_version)
print_info "Current version: $current_version"
echo ""

# Ask for version bump type or custom version
echo "Select version bump type:"
echo "  1) Patch (bug fixes)          → $(increment_version "$current_version" patch)"
echo "  2) Minor (new features)       → $(increment_version "$current_version" minor)"
echo "  3) Major (breaking changes)   → $(increment_version "$current_version" major)"
echo "  4) Custom version"
echo "  5) Cancel"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        new_version=$(increment_version "$current_version" patch)
        ;;
    2)
        new_version=$(increment_version "$current_version" minor)
        ;;
    3)
        new_version=$(increment_version "$current_version" major)
        ;;
    4)
        read -p "Enter custom version: " new_version
        if [[ ! $new_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            print_error "Invalid version format. Use semantic versioning (e.g., 1.2.3)"
            exit 1
        fi
        ;;
    5)
        print_info "Release cancelled"
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_info "New version will be: $new_version"
echo ""

# Confirm release
read -p "Proceed with release? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Release cancelled"
    exit 0
fi

echo ""
print_info "Starting release process..."
echo ""

# Step 1: Update version in pyproject.toml
print_info "Updating version in pyproject.toml..."
update_version "$new_version"
print_success "Version updated to $new_version"

# Step 2: Update CHANGELOG.md
print_info "Generating CHANGELOG.md from commits..."
add_changelog_entry "$new_version"
print_success "Changelog generated"

# Show preview
echo ""
print_info "Changelog preview:"
echo "─────────────────────────────────────────────────────────────"
head -n 20 CHANGELOG.md
echo "─────────────────────────────────────────────────────────────"
echo ""

# Open editor for changelog
read -p "Edit CHANGELOG.md before continuing? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v ${EDITOR:-nano} &> /dev/null; then
        print_info "Opening CHANGELOG.md for editing..."
        ${EDITOR:-nano} CHANGELOG.md
    else
        print_warning "No editor found. Please manually edit CHANGELOG.md"
        read -p "Press Enter when done editing..."
    fi
fi

# Step 3: Clean previous builds
print_info "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info
print_success "Build artifacts cleaned"

# Step 4: Build package
print_info "Building package..."
if ! python -m build; then
    print_error "Build failed"
    exit 1
fi
print_success "Package built successfully"

# Step 5: Check package with twine
print_info "Checking package..."
if ! python -m twine check dist/*; then
    print_error "Package check failed"
    exit 1
fi
print_success "Package check passed"

# Step 6: Commit changes
print_info "Committing changes..."
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release version $new_version"
print_success "Changes committed"

# Step 7: Create git tag
print_info "Creating git tag v$new_version..."
git tag -a "v$new_version" -m "Release version $new_version"
print_success "Git tag created"

# Step 8: Ask about PyPI upload
echo ""
print_warning "Ready to upload to PyPI"
echo ""
echo "Choose upload destination:"
echo "  1) TestPyPI (recommended for testing)"
echo "  2) PyPI (production)"
echo "  3) Skip upload"
echo ""
read -p "Enter choice [1-3]: " upload_choice

case $upload_choice in
    1)
        print_info "Uploading to TestPyPI..."
        if python -m twine upload --repository testpypi dist/*; then
            print_success "Package uploaded to TestPyPI"
            echo ""
            print_info "Test installation with:"
            echo "  pip install --index-url https://test.pypi.org/simple/ trello-mcp-server==$new_version"
        else
            print_error "Upload to TestPyPI failed"
            exit 1
        fi
        ;;
    2)
        print_info "Uploading to PyPI..."
        if python -m twine upload dist/*; then
            print_success "Package uploaded to PyPI"
            echo ""
            print_info "Install with:"
            echo "  pip install trello-mcp-server==$new_version"
            echo "  uvx trello-mcp-server"
        else
            print_error "Upload to PyPI failed"
            exit 1
        fi
        ;;
    3)
        print_info "Skipping upload"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Step 9: Push to git
echo ""
read -p "Push changes and tags to remote? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Pushing to remote..."
    git push origin "$current_branch"
    git push origin "v$new_version"
    print_success "Changes and tags pushed to remote"
else
    print_warning "Changes not pushed. Remember to push manually:"
    echo "  git push origin $current_branch"
    echo "  git push origin v$new_version"
fi

echo ""
print_success "═══════════════════════════════════════════════════════════"
print_success "  Release $new_version completed successfully!"
print_success "═══════════════════════════════════════════════════════════"
echo ""

# Show summary
print_info "Summary:"
echo "  • Version: $current_version → $new_version"
echo "  • Git tag: v$new_version"
echo "  • Package: dist/trello_mcp_server-$new_version-py3-none-any.whl"
echo ""

if [[ $upload_choice == "2" ]]; then
    print_info "Next steps:"
    echo "  • Verify installation: uvx trello-mcp-server"
    echo "  • Check PyPI page: https://pypi.org/project/trello-mcp-server/"
    echo "  • Create GitHub release (optional)"
fi

echo ""
