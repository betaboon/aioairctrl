from setuptools import setup, find_packages

setup(
    name="aioairctrl",
    description="library for controlling philips air purifiers (using encrypted CoAP)",
    author="betaboon",
    url="https://github.com/betaboon/aioairctrl",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "aiocoap==0.4b3",
        "pycryptodomex",
    ],
    entry_points={
        "console_scripts": [
            "aioairctrl=aioairctrl.__main__:main",
        ],
    },
)
