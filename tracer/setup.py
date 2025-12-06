"""
Setup script for memtrace Python package.
"""

from setuptools import setup, find_packages
import os


# Read README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()


setup(
    name="memlyze",
    version="0.1.0",
    author="Memlyze Team",
    description="Visual memory profiler with <5% overhead",
    long_description=read_file("../README.md") if os.path.exists("../README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/rarfile/memlyze",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies for Phase 1!
    ],
    entry_points={
        "console_scripts": [
            "memlyze=memlyze.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
