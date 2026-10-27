from setuptools import setup, find_packages

setup(
    name="ai-code-reviewer",
    version="1.0.0",
    description="AST-based Automated Python Code Reviewer and Quality Scoring System",
    author="Pranjal Kute, Janhavi Phadke, Siyona Pande, Anushka Kadam",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ai-review=cli:main",
        ],
    },
    python_requires=">=3.8",
)
