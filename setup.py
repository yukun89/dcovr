import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dcovr-yukun89",
    version="0.0.1",
    author="huangyukun",
    author_email="huangyukun@2012@163.com",
    description="A tool to generage delta coverage report based on gcovr",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yukun89/dcovr",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
