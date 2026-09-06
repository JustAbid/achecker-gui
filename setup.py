from setuptools import find_packages, setup

setup(
    name="AChecker",
    version="0.1.0",
    description="Static analyzer for smart-contract access-control vulnerabilities, with a Flask web interface.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/JustAbid/achecker-gui",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={"achecker_gui": ["templates/*.html", "static/css/*.css", "static/js/*.js"]},
    scripts=["bin/achecker.py"],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
    ],
)
