from setuptools import setup, find_packages

setup(
    name="avatarai",
    version="0.1.0",
    description="Anything to avatar",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="zhongshangwu",
    author_email="zhongshangwu07@gmail.com",
    url="https://github.com/zhongshangwu/avatarai",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "pillow>=8.0.0",
        "torch>=1.9.0",
        "transformers>=4.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
