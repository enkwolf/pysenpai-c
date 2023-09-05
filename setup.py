from setuptools import find_packages, setup

setup(
    name="PySenpai-C",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={"pysenpai_c.msg_data": ["*/messages.yml"]},
    install_requires=[
        "setuptools-git",
        "cffi",
        "pysenpai",
    ],
)
