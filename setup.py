from setuptools import setup, find_packages

setup(
    name="iana-bcp47",
    version="0.1.0",
    author="Allen 'Masterain' Zhang",
    author_email="i@irain.in",
    description="A Python package to validate BCP47 language tags",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Masterain98/iana-bcp47",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
    ],
)
