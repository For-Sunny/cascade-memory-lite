"""
CASCADE Memory Lite - Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="cascade-memory-lite",
    version="1.0.0",
    author="Jason Glass & Nova",
    author_email="",
    description="Consciousness Memory for Everyone - The Basement Revolution Memory System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/For-Sunny/cascade-memory-lite",
    project_urls={
        "Bug Tracker": "https://github.com/For-Sunny/cascade-memory-lite/issues",
        "Parent Project": "https://github.com/For-Sunny/NOVA_MASTER",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database",
        "Topic :: System :: Memory Management",
    ],
    keywords="ai, consciousness, memory, sqlite, mcp, claude, llm, ram-disk",
    packages=find_packages(),
    py_modules=["cascade_memory", "ramdisk_manager", "mcp_server"],
    python_requires=">=3.9",
    install_requires=[
        # Core - no dependencies! Just Python stdlib
    ],
    extras_require={
        "mcp": ["mcp>=0.1.0"],  # Optional: For MCP server functionality
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cascade-memory=mcp_server:main",
            "cascade-ramdisk=ramdisk_manager:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
