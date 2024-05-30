from setuptools import setup, find_packages
import os

def read_requirements():
    with open('requirements.txt') as req_file:
        return req_file.read().splitlines()

def read_long_description():
    with open('README.md') as readme_file:
        return readme_file.read()

setup(
    name='eurlex-parser',
    version='0.0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=['eurlex'],
    include_package_data=True,
    install_requires=read_requirements(),
    description='Eurlex parser for fetching and parsing Eurlex data.',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    author='Yan-Ying Liao',
    author_email='n9102125@gmail.com',
    url='https://github.com/noworneverev/eurlex-parser',
    classifiers=[],
    python_requires='>=3.6',
)