# Release Process

This document describes how to release new versions of the Trello MCP Server to PyPI.

## Prerequisites

1. Install build tools:
```bash
pip install build twine
```

2. Set up PyPI credentials:
   - Create account at https://pypi.org/account/register/
   - Enable 2FA (required)
   - Generate API token at https://pypi.org/manage/account/token/
   - Store in `~/.pypirc`:
   ```ini
   [pypi]
   username = __token__
   password = pypi-your-api-token-here
   
   [testpypi]
   username = __token__
   password = pypi-your-testpypi-token-here
   ```

## Release Methods

### Method 1: Interactive Release Script (Recommended)

Use the interactive release script for full control:

```bash
./release.sh
```

This script will:
1. Check git status and branch
2. Prompt for version bump type (patch/minor/major) or custom version
3. Update `pyproject.toml` with new version
4. Auto-generate changelog from git commits (supports conventional commits)
5. Show preview and optionally open editor for manual adjustments
6. Build the package
7. Run package checks
8. Commit changes and create git tag
9. Optionally upload to TestPyPI or PyPI
10. Optionally push to remote

The script automatically categorizes commits using conventional commit format:
- `feat:` → Added section
- `fix:` → Fixed section
- `refactor:`, `perf:`, `style:`, `docs:`, `chore:` → Changed section

### Method 2: Quick Patch Release

For quick bug fix releases with auto-generated changelog:

```bash
./quick-release.sh
```

Or with a custom description:

```bash
./quick-release.sh "Fix authentication timeout issue"
```

This automatically:
- Increments patch version
- Generates changelog from commits (or uses provided description)
- Builds package
- Creates commit and tag

Then manually:
```bash
python -m twine upload dist/*
git push && git push --tags
```

### Method 3: Manual Release

1. Update version in `pyproject.toml`:
```toml
version = "1.2.3"
```

2. Update `CHANGELOG.md`:
```markdown
## [1.2.3] - 2024-01-15

### Added
- New feature description

### Fixed
- Bug fix description
```

3. Build package:
```bash
rm -rf dist/ build/ *.egg-info
python -m build
```

4. Check package:
```bash
python -m twine check dist/*
```

5. Upload to TestPyPI (optional):
```bash
python -m twine upload --repository testpypi dist/*
```

6. Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ trello-mcp-server==1.2.3
```

7. Upload to PyPI:
```bash
python -m twine upload dist/*
```

8. Commit and tag:
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release version 1.2.3"
git tag -a v1.2.3 -m "Release version 1.2.3"
git push && git push --tags
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, backward compatible

## Changelog Format

The release scripts automatically generate changelog entries from git commits. For best results, use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Features (→ Added section)
git commit -m "feat: add support for custom fields"
git commit -m "feat(cards): add due date reminder tool"

# Bug fixes (→ Fixed section)
git commit -m "fix: resolve authentication timeout"
git commit -m "fix(auth): handle expired tokens gracefully"

# Other changes (→ Changed section)
git commit -m "refactor: simplify API client code"
git commit -m "docs: update authentication guide"
git commit -m "chore: update dependencies"
```

Manual changelog format follows [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [Version] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes
```

## Testing Before Release

1. Run tests:
```bash
python -m pytest
python test_auth.py
python test_organizations.py
```

2. Test local installation:
```bash
pip install -e .
python -m trello_mcp_server --help
```

3. Test authentication:
```bash
python -m trello_mcp_server.auth --check
```

## Post-Release

1. Verify PyPI page: https://pypi.org/project/trello-mcp-server/
2. Test installation:
```bash
uvx trello-mcp-server
```
3. Create GitHub release (optional):
   - Go to https://github.com/cargom98/gm-trello-mcp/releases
   - Click "Draft a new release"
   - Select the tag
   - Copy changelog entry
   - Publish release

## Troubleshooting

### Upload fails with "File already exists"
- You cannot overwrite a version on PyPI
- Increment version and try again

### Authentication fails
- Check `~/.pypirc` has correct token
- Verify token hasn't expired
- Try re-generating token

### Package check fails
- Review error messages
- Common issues: missing README, invalid metadata
- Fix and rebuild

### Git tag already exists
```bash
# Delete local tag
git tag -d v1.2.3

# Delete remote tag
git push origin :refs/tags/v1.2.3
```

## Rollback

If you need to rollback a release:

1. You cannot delete versions from PyPI (by design)
2. Release a new patch version with fixes
3. Mark the problematic version as "yanked" on PyPI (prevents new installs)

## CI/CD (Future)

Consider setting up GitHub Actions for automated releases:
- Trigger on git tags
- Run tests
- Build package
- Upload to PyPI
- Create GitHub release
