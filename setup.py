from setuptools import setup, find_packages

setup(
    name="terminal-coding-agent",
    version="0.1.0",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.10",
    install_requires=[
        "anthropic",
        "PyYAML",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "coding-agent=src.cli:main", # activates once cli.py defines main()
        ],
    },
)