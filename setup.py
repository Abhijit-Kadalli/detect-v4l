from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="detect_v4ln",
    version="0.1.0",
    author="Abhijit Kadalli",
    author_email="abhijitkadalli14@gmail.com",
    description="A library to detect and identify Video4Linux cameras",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Abhijit-Kadalli/detect_v4ln",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
)