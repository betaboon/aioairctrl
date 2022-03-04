from setuptools import setup, find_packages

setup(
    name="aioairctrl",
    version="0.2.2",
    description="library for controlling philips air purifiers (using encrypted CoAP)",
    author="balu-",
    url="https://github.com/balu-/aioairctrl",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "aiocoap==0.4.3",
        "pycryptodomex",
    ],
    entry_points={
        "console_scripts": [
            "aioairctrl=aioairctrl.__main__:main",
        ],
    },
)
