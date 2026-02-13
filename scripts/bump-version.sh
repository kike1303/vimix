#!/usr/bin/env bash
# Bump the version across all Vimix config files.
#
# Usage:
#   ./scripts/bump-version.sh 0.2.0
#
# Updates version in:
#   1. package.json (root)
#   2. apps/web/package.json
#   3. apps/web/src-tauri/tauri.conf.json
#   4. apps/web/src-tauri/Cargo.toml
#   5. services/processor/app/main.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ $# -ne 1 ]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 0.2.0"
  exit 1
fi

VERSION="$1"

# Validate semver format (major.minor.patch, optional pre-release)
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
  echo "Error: '$VERSION' is not a valid semver version (e.g. 1.2.3 or 1.2.3-rc.1)"
  exit 1
fi

echo "Bumping version to $VERSION"
echo ""

# 1. Root package.json
node -e "
const fs = require('fs');
const path = '$PROJECT_ROOT/package.json';
const pkg = JSON.parse(fs.readFileSync(path, 'utf8'));
pkg.version = '$VERSION';
fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n');
"
echo "  ✓ package.json"

# 2. apps/web/package.json
node -e "
const fs = require('fs');
const path = '$PROJECT_ROOT/apps/web/package.json';
const pkg = JSON.parse(fs.readFileSync(path, 'utf8'));
pkg.version = '$VERSION';
fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n');
"
echo "  ✓ apps/web/package.json"

# 3. apps/web/src-tauri/tauri.conf.json
node -e "
const fs = require('fs');
const path = '$PROJECT_ROOT/apps/web/src-tauri/tauri.conf.json';
const conf = JSON.parse(fs.readFileSync(path, 'utf8'));
conf.version = '$VERSION';
fs.writeFileSync(path, JSON.stringify(conf, null, 2) + '\n');
"
echo "  ✓ apps/web/src-tauri/tauri.conf.json"

# 4. apps/web/src-tauri/Cargo.toml — use platform-aware sed
CARGO_TOML="$PROJECT_ROOT/apps/web/src-tauri/Cargo.toml"
if [[ "$(uname -s)" == "Darwin" ]]; then
  sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" "$CARGO_TOML"
else
  sed -i "s/^version = \".*\"/version = \"$VERSION\"/" "$CARGO_TOML"
fi
echo "  ✓ apps/web/src-tauri/Cargo.toml"

# 5. services/processor/app/main.py — update version= in FastAPI constructor
MAIN_PY="$PROJECT_ROOT/services/processor/app/main.py"
if [[ "$(uname -s)" == "Darwin" ]]; then
  sed -i '' "s/version=\"[^\"]*\"/version=\"$VERSION\"/" "$MAIN_PY"
else
  sed -i "s/version=\"[^\"]*\"/version=\"$VERSION\"/" "$MAIN_PY"
fi
echo "  ✓ services/processor/app/main.py"

echo ""
echo "Version bumped to $VERSION in all 5 files."
echo ""
echo "Next steps:"
echo "  1. Update CHANGELOG.md with the new version's changes"
echo "  2. git add -A && git commit -m \"chore: bump version to $VERSION\""
echo "  3. git tag v$VERSION"
echo "  4. git push origin main --tags"
