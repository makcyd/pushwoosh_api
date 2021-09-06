from setuptools import setup

setup(
    name="pushwoosh_api",
    version="0.0.10",
    description="Python wrapper for Pushwoosh API",
    url="https://docs.pushwoosh.com/platform-docs/api-reference/",
    author="Max Sudyin",
    author_email="msudyin@pushwoosh.com",
    license="MIT",
    packages=["pushwoosh_api"],
    install_requires=[
        "requests",
        "tenacity"
    ],
    zip_safe=False
)
