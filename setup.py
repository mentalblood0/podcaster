import pathlib

import setuptools

if __name__ == "__main__":
    setuptools.setup(
        name="podcaster",
        version="1.4.0",
        description="Upload audio from youtube to telegram channels",
        long_description=(pathlib.Path(__file__).parent / "README.md").read_text(),
        long_description_content_type="text/markdown",
        author="mentalblood",
        packages=setuptools.find_packages(exclude=["tests*"]),
        install_requires=["click", "yoop"],
    )
