from setuptools import setup

setup(
    name="jsonquery",
    version="1.0.0",
    description="Smart JSON Query & Filter Tool - zero external dependencies",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Logan Smith / Metaphy LLC",
    author_email="logan@metaphy.com",
    url="https://github.com/DonkRonk17/JSONQuery",
    py_modules=["jsonquery"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "jsonquery=jsonquery:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    keywords="json query filter cli jsonpath search tool",
)
