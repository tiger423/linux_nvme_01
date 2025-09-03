#!/usr/bin/env python3
"""
Setup script for Linux NVMe Information Command Test
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Enterprise-grade NVMe SSD reliability test program"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Handle version specifiers
                    if '>=' in line or '==' in line or '<=' in line:
                        requirements.append(line)
                    elif line:
                        requirements.append(line)
    return requirements

setup(
    name="linux-nvme-01",
    version="1.0.0",
    author="tiger423",
    author_email="",
    description="Enterprise-grade NVMe SSD reliability test program implementing linux_nvme_information_cmd specification",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/tiger423/linux_nvme_01",
    project_urls={
        "Bug Reports": "https://github.com/tiger423/linux_nvme_01/issues",
        "Source": "https://github.com/tiger423/linux_nvme_01",
        "Documentation": "https://github.com/tiger423/linux_nvme_01/blob/main/README.md",
    },
    
    # Package configuration
    packages=find_packages(),
    py_modules=[
        'main',
        'nvme_test_executor',
        'nvme_cli_interface', 
        'result_analyzer',
        'config_parser',
        'test_logger'
    ],
    
    # Python version requirement
    python_requires=">=3.6",
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Entry points
    entry_points={
        'console_scripts': [
            'nvme-info-test=main:main',
            'linux-nvme-01=main:main',
        ],
    },
    
    # Package data
    package_data={
        '': ['*.yaml', '*.yml', '*.txt', '*.md'],
    },
    include_package_data=True,
    
    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Topic :: System :: Hardware",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],
    
    # Keywords for discovery
    keywords="nvme ssd test reliability enterprise storage hardware validation",
    
    # Additional metadata
    zip_safe=False,
    platforms=['Linux'],
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=6.0',
            'flake8>=3.8',
            'black>=21.0',
            'mypy>=0.910',
        ],
        'testing': [
            'pytest>=6.0',
            'pytest-cov>=2.10',
            'pytest-mock>=3.0',
        ],
    },
    
    # System requirements note
    install_requires_notes="""
    System Requirements:
    - Linux operating system
    - NVMe CLI tools (install with package manager)
    - Root privileges for NVMe device access
    - Python 3.6 or higher
    
    Install nvme-cli:
    - Ubuntu/Debian: sudo apt-get install nvme-cli
    - RHEL/CentOS: sudo yum install nvme-cli
    - Fedora: sudo dnf install nvme-cli
    """,
)