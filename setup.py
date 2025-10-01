
# Licensed under GPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="GateAssignmentDirector",
    version="0.6.0",
    author="GateAssignmentDirector",
    author_email="GateAssigmentDirector@s1.mozmail.com",
    description="Bridge between SayIntentions AI and GSX gate assignment for MSFS 2020",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/SayIntentionsBridge",  # TODO: Update when published
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment :: Simulation",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gate-director=GateAssignmentDirector.director:main",
            "gate-director-ui=GateAssignmentDirector.ui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "GateAssignmentDirector": ["*.png", "*.yaml"],
    },
)