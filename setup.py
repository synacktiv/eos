from os import path
from setuptools import setup, find_packages

import eos


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='eos',
    version=eos.__version__,
    description='Enemies Of Symfony',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/synacktiv/eos',
    author='Synacktiv',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='scanner symfony eos enemies-of-symfony',
    packages=find_packages(),
    python_requires='>=3.5, <4',
    install_requires=[
        'requests',
        'beautifulsoup4',
        'lxml',
    ],
    package_data={
        'eos': ['wordlist.txt'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['eos=eos.__main__:main'],
    },
    project_urls={
        'Symfony': 'https://symfony.com',
        'Apply!': 'https://www.synacktiv.com',
        'Source': 'https://github.com/synacktiv/eos',
    },
)
