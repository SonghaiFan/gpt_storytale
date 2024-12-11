from setuptools import setup, find_packages

setup(
    name="gpt_storytale",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'openai',
        'python-dotenv',
        'pathlib',
    ],
) 