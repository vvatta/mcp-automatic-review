"""Setup script for MCP Malware Sandbox."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mcp-malware-sandbox",
    version="0.1.0",
    author="MCP Security Team",
    description="Comprehensive MCP malware sandbox with layered security architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vvatta/mcp-automatic-review",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mcp-sandbox=src.cli:main",
        ],
    },
)
