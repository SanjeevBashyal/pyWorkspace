from setuptools import setup, find_packages
import os

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pyworkspace",  # You may need to change this if the name is already taken on PyPI
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A python workspace and session manager for Windows environments with hotkey support.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SanjeevBashyal/pyWorkspace",
    packages=find_packages(),
    install_requires=[
        "keyboard>=0.13.5",
    ],
    # This creates a command line executable, so users can just type 'pyworkspace-service'
    entry_points={
        "console_scripts": [
            "pyworkspace-service=pyworkspace.service:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Win32 (MS Windows)",
    ],
    python_requires=">=3.6",
)
