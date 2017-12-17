#!/usr/bin/env python

from setuptools import setup


version = '0.2.0'

with open('README.rst', 'r') as f:
    readme = f.read()

packages = [
    'netdumplings',
    'netdumplings.console',
    'netdumplings.dumplingchefs'
]

install_requires = [
    'scapy-python3==0.23',
    'websockets~=4.0.0',
]

tests_require = [
    'pytest',
    'pytest-cov',
    'pytest-mock',
    'pytest-sugar',
]

extras_require = {
    'dev': [
        'flake8',
        'sphinx',
    ] + tests_require,
}

setup(
    name='netdumplings',
    version=version,
    description='Tools for building your own computer network visualizations.',
    long_description=readme,
    author='Mike Joblin',
    author_email='mike@tastymoss.com',
    url='https://github.com/mjoblin/netdumplings',
    packages=packages,
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    download_url='https://pypi.python.org/pypi/netdumplings',
    entry_points={
        'console_scripts': [
            'nd-snifty=netdumplings.console:snifty',
            'nd-shifty=netdumplings.console:shifty',
            'nd-info=netdumplings.console:info',
            'nd-status=netdumplings.console:status',
            'nd-printer=netdumplings.console:printer',
        ]
    },
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking',
        'Topic :: System :: Networking :: Monitoring',
    ]
)
