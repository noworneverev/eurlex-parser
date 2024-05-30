from setuptools import setup, find_packages
import os

VERSION = '0.0.2'  
DESCRIPTION  = 'Eurlex parser for fetching and parsing Eurlex data.'

def read_requirements():
    with open('requirements.txt') as req_file:
        return req_file.read().splitlines()

def read_long_description():
    with open('README.md', encoding='utf-8') as readme_file:
        return readme_file.read()

setup(
    name='eurlex-parser',
    version=VERSION,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=['eurlex'],
    include_package_data=True,
    install_requires=read_requirements(),
    description=DESCRIPTION,
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    author='Yan-Ying Liao',
    author_email='n9102125@gmail.com',
    url='https://github.com/noworneverev/eurlex-parser',
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    
    python_requires='>=3.6',
)