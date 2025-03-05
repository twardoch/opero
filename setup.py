#!/usr/bin/env python3
# this_file: setup.py

import os
from setuptools import setup, find_packages

# Read the contents of the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read the version from version.py
version = {}
with open(os.path.join("src", "opero", "version.py"), encoding="utf-8") as f:
    exec(f.read(), version)

setup(
    name="opero",
    version=version["__version__"],
    description="Resilient, Parallel Task Orchestration for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Adam Twardoch",
    author_email="adam@twardoch.com",
    url="https://github.com/twardoch/opero",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="resilience, retry, fallback, cache, rate-limit, parallel, async",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "twat-cache>=0.1.0",
        "twat-mp>=0.1.0",
    ],
    extras_require={
        "dev": [
            "black",
            "isort",
            "mypy",
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "ruff",
        ],
        "redis": ["redis"],
    },
    project_urls={
        "Bug Reports": "https://github.com/twardoch/opero/issues",
        "Source": "https://github.com/twardoch/opero",
    },
)
