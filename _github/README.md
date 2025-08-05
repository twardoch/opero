# GitHub Actions Workflows

This directory contains the planned GitHub Actions workflows for the Opero project.

## Workflows

### `push.yml` - Build & Test
**Triggers:** Push to main, Pull Requests, Manual dispatch

- **Code Quality**: Runs Ruff linting and formatting checks
- **Tests**: Runs pytest across Python 3.10, 3.11, and 3.12 on Ubuntu
- **Build**: Creates distribution packages (wheel and source)
- **Documentation Check**: Validates MkDocs configuration when docs files change

### `release.yml` - Release to PyPI
**Triggers:** Version tags (v*)

- Builds distribution packages
- Publishes to PyPI using trusted publishing
- Creates GitHub release with artifacts

### `docs.yml` - Build and Deploy Documentation
**Triggers:** Push to main, Pull Requests affecting docs, Manual dispatch

- **Build**: Compiles MkDocs documentation from `src_docs/` to `docs/`
- **Deploy**: Deploys to GitHub Pages (main branch only)
- **Preview**: Provides build status for Pull Requests

## Documentation Setup

The documentation system uses:

- **Source**: `src_docs/md/` - Markdown documentation files
- **Config**: `src_docs/mkdocs.yml` - MkDocs configuration with Material theme
- **Output**: `docs/` - Built static site for GitHub Pages
- **Theme**: Material for MkDocs with advanced features

### Documentation Structure

```
src_docs/
├── mkdocs.yml                 # MkDocs configuration
└── md/                        # Documentation content
    ├── index.md              # Homepage with TOC and TLDR
    ├── getting-started/      # Installation, quickstart, configuration
    │   ├── installation.md
    │   ├── quickstart.md
    │   └── configuration.md
    ├── guide/                # User guides
    │   ├── basic-usage.md
    │   ├── advanced-features.md
    │   └── best-practices.md
    └── api/                  # API reference
        ├── overview.md
        ├── core.md
        └── utils.md
```

### MkDocs Features Enabled

- **Material Theme**: Modern, responsive documentation theme
- **Navigation**: Tabs, sections, and path breadcrumbs
- **Search**: Full-text search with highlighting
- **Code**: Syntax highlighting with copy buttons
- **Git Integration**: Last modified dates and contributors
- **Optimization**: Minified HTML/CSS/JS for faster loading
- **Social**: Open Graph meta tags for link previews

## Setup Instructions

To use these workflows:

1. **Copy to .github**: Move contents from `_github/` to `.github/`
   ```bash
   cp -r _github/ .github/
   ```

2. **Enable GitHub Pages**: 
   - Go to repository Settings → Pages
   - Set source to "GitHub Actions"

3. **Configure Secrets** (for releases):
   - `PYPI_TOKEN`: PyPI API token for package publishing

4. **Test Documentation Locally**:
   ```bash
   cd src_docs
   pip install mkdocs-material mkdocs-git-revision-date-localized-plugin mkdocs-git-committers-plugin-2 mkdocs-minify-plugin
   mkdocs serve
   ```

## Workflow Dependencies

The workflows require these GitHub Actions:

- `actions/checkout@v4` - Code checkout
- `actions/setup-python@v5` - Python environment
- `astral-sh/setup-uv@v5` - UV package manager
- `astral-sh/ruff-action@v3` - Ruff linting
- `actions/upload-artifact@v4` - Artifact uploads
- `actions/configure-pages@v4` - GitHub Pages setup
- `actions/upload-pages-artifact@v3` - Pages deployment
- `actions/deploy-pages@v4` - Pages deployment
- `pypa/gh-action-pypi-publish@release/v1` - PyPI publishing
- `softprops/action-gh-release@v1` - GitHub releases

## Maintenance

- **Dependencies**: Update action versions regularly in `dependabot.yml`
- **Python Versions**: Update test matrix as Python versions are released/deprecated
- **Documentation**: Keep MkDocs and plugins updated for security and features
- **Monitoring**: Check workflow success rates and adjust timeouts/retry logic as needed