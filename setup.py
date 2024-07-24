"""qsi installation configuration"""

from setuptools import find_packages, setup
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
setup(
    name="qsi",
    version="0.0.2",
    author="Simon Sekavčnik",
    author_email="simon.sekavcnik@tum.de",
    description="Communication interface implementation for special issue",
    license="Apache 2.0",
    packages=find_packages(where="."),
    install_requires=[
    ],
)
