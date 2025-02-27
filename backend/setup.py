"""Setup script for the backend package."""

from setuptools import setup, find_packages

setup(
    name="financial-statement-parser",
    version="1.0.0",
    description="Financial statement parsing and analysis using AI",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai>=1.0.0",
        "google-genai>=0.3.0",
        "pdf2image>=1.16.0",
        "PyPDF2>=3.0.0",
        "Pillow>=9.0.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "statement-parser=backend.src.main:main",
            "statement-api=backend.src.api.server:main",
        ],
    },
    python_requires=">=3.8",
) 