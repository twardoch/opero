# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the Opero project.

## Workflows

### `push.yml` - Build & Test
**Triggers:** Push to main, pull requests, manual dispatch

- **Code Quality**: Runs Ruff linting and formatting checks
- **Tests**: Runs pytest on Python 3.10, 3.11, and 3.12 (Ubuntu only)
- **Build**: Creates wheel and source distribution packages
- **Documentation Check**: Validates MkDocs config when docs files change

### `release.yml` - Release to PyPI
**Triggers:** Version tags (`v*`)

- Builds distribution packages
- Publishes to PyPI using trusted publishing
- Creates a GitHub release with uploaded artifacts

### `docs.yml` - Build and Deploy Documentation
**Triggers:** Push to main, pull requests affecting docs, manual dispatch

- **Build**: Compiles MkDocs documentation from `src_docs/` to `docs/`
- **Deploy**: Deploys built docs to GitHub Pages (main branch only)
- **Preview**: Reports build status for pull request documentation changes

## Documentation Setup

The documentation system uses:

- **Source**: `src_docs/md/` – Markdown files
- **Config**: `src_docs/mkdocs.yml` – MkDocs configuration with Material theme
- **Output**: `docs/` – Static site output for GitHub Pages
- **Theme**: Material for MkDocs

### Documentation Structure

```
src_docs/
├── mkdocs.yml                 # Configuration
└── md/                        # Content
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

### MkDocs Features

- Material theme
- Tabbed navigation and breadcrumbs
- Full-text search with highlighting
- Syntax highlighting and copy buttons
- Git integration: last modified dates, contributors
- Minified HTML/CSS/JS for faster loading
- Open Graph meta tags for link previews

## Setup Instructions

To enable these workflows:

1. **Move workflow files**
   ```bash
   cp -r _github/ .github/
   ```

2. **Enable GitHub Pages**  
   Go to repository Settings → Pages → Set source to "GitHub Actions"

3. **Set up secrets** (for releases)  
   Add `PYPI_TOKEN`: your PyPI API token

4. **Test docs locally**
   ```bash
   cd src_docs
   pip install mkdocs-material \
               mkdocs-git-revision-date-localized-plugin \
               mkdocs-git-committers-plugin-2 \
               mkdocs-minify-plugin
   mkdocs serve
   ```

## Workflow Dependencies

These GitHub Actions are used:

- `actions/checkout@v4`
- `actions/setup-python@v5`
- `astral-sh/setup-uv@v5`
- `astral-sh/ruff-action@v3`
- `actions/upload-artifact@v4`
- `actions/configure-pages@v4`
- `actions/upload-pages-artifact@v3`
- `actions/deploy-pages@v4`
- `pypa/gh-action-pypi-publish@release/v1`
- `softprops/action-gh-release@v1`

## Maintenance

- Update action versions in `dependabot.yml` regularly
- Refresh Python version matrix as versions evolve
- Keep MkDocs and plugins current
- Monitor workflow success and tune timeouts or retries if needed