from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="pyworkspace",
    version="1.0.0",
    description="A Python-based Windows Virtual Desktop workspace manager.",
    author="Ripple",
    packages=find_packages(),
    py_modules=["UI"],
    install_requires=[
        "PyQt6",
        "psutil",
        "pywin32",
        "comtypes",
        "google-auth",
        "gspread",
        "pyvda"
    ],
    entry_points={
        "console_scripts": [
            "pyworkspace=UI:main",
        ]
    },
)
