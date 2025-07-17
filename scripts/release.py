#!/usr/bin/env python3
"""
Release script for the opero package.
"""

import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    
    if result.stdout:
        print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    
    return result


def get_current_version() -> str:
    """Get the current version from git tags."""
    try:
        result = run_command("git describe --tags --abbrev=0")
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "v0.0.0"


def increment_version(version: str, increment_type: str = "patch") -> str:
    """Increment version number."""
    # Remove 'v' prefix if present
    version = version.lstrip('v')
    
    # Parse version
    parts = version.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    elif increment_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid increment type: {increment_type}")
    
    return f"v{major}.{minor}.{patch}"


def validate_version(version: str) -> bool:
    """Validate version format."""
    pattern = r'^v?\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def check_working_directory_clean() -> bool:
    """Check if working directory is clean."""
    try:
        result = run_command("git status --porcelain")
        return len(result.stdout.strip()) == 0
    except subprocess.CalledProcessError:
        return False


def main():
    """Main release function."""
    repo_root = Path(__file__).parent.parent
    print(f"Repository root: {repo_root}")
    
    # Parse command line arguments
    increment_type = "patch"
    if len(sys.argv) > 1:
        increment_type = sys.argv[1]
        if increment_type not in ["major", "minor", "patch"]:
            print(f"❌ Invalid increment type: {increment_type}")
            print("Usage: python release.py [major|minor|patch]")
            sys.exit(1)
    
    # Check working directory is clean
    if not check_working_directory_clean():
        print("❌ Working directory is not clean. Please commit or stash changes first.")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Calculate new version
    new_version = increment_version(current_version, increment_type)
    print(f"New version: {new_version}")
    
    # Confirm release
    confirm = input(f"Create release {new_version}? (y/N): ")
    if confirm.lower() != 'y':
        print("Release cancelled.")
        sys.exit(0)
    
    # Run build script
    print("🔨 Running build script...")
    try:
        run_command("python scripts/build.py", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
    
    # Run tests
    print("🧪 Running tests...")
    try:
        run_command("python scripts/test.py", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        sys.exit(1)
    
    # Update CHANGELOG.md
    print("📝 Updating CHANGELOG.md...")
    changelog_path = repo_root / "CHANGELOG.md"
    if changelog_path.exists():
        with open(changelog_path, 'r') as f:
            content = f.read()
        
        # Add new version entry
        import datetime
        today = datetime.date.today().isoformat()
        new_entry = f"## [{new_version.lstrip('v')}] - {today}\n\n### Added\n- Release {new_version}\n\n"
        
        # Insert after the [Unreleased] section
        if "## [Unreleased]" in content:
            content = content.replace("## [Unreleased]", f"## [Unreleased]\n\n{new_entry}")
        else:
            content = new_entry + content
        
        with open(changelog_path, 'w') as f:
            f.write(content)
        
        # Commit changelog update
        run_command("git add CHANGELOG.md", cwd=repo_root)
        run_command(f"git commit -m 'docs: update changelog for {new_version}'", cwd=repo_root)
    
    # Create git tag
    print(f"🏷️  Creating git tag {new_version}...")
    try:
        run_command(f"git tag -a {new_version} -m 'Release {new_version}'", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create tag: {e}")
        sys.exit(1)
    
    # Push to origin
    print("🚀 Pushing to origin...")
    try:
        run_command("git push origin main", cwd=repo_root)
        run_command(f"git push origin {new_version}", cwd=repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to push: {e}")
        print("Tag created locally but not pushed. Push manually with:")
        print(f"  git push origin main")
        print(f"  git push origin {new_version}")
        sys.exit(1)
    
    print(f"✅ Release {new_version} completed successfully!")
    print(f"🎉 GitHub Actions will automatically build and publish the release.")


if __name__ == "__main__":
    main()