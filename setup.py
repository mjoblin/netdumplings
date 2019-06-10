import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(here, 'netdumplings', '_version.py')) as ver_file:
    exec(ver_file.read(), version)

with open(os.path.join(here, 'README.rst'), 'r') as f:
    readme = f.read()

packages = [
    'netdumplings',
    'netdumplings.console',
    'netdumplings.dumplingchefs',
]

install_requires = [
    'click~=6.7',
    'netifaces',
    'pygments',
    'scapy~=2.4.2',
    'termcolor',
    'websockets~=7.0.0',
]

tests_require = [
    'asynctest',
    'pytest',
    'pytest-asyncio',
    'pytest-cov',
    'pytest-mock',
    'pytest-sugar',
]

extras_require = {
    'dev': [
        'flake8',
        'mypy',
        'sphinx',
        'sphinx-autodoc-typehints',
    ] + tests_require,
}

setup(
    name='netdumplings',
    version=version['__version__'],
    description=(
        'A framework for distributed network packet sniffing and processing.'
    ),
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
            'nd-hub=netdumplings.console:hub_cli',
            'nd-hubdetails=netdumplings.console:hubdetails_cli',
            'nd-hubstatus=netdumplings.console:hubstatus_cli',
            'nd-print=netdumplings.console:print_cli',
            'nd-sniff=netdumplings.console:sniff_cli',
        ]
    },
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking',
        'Topic :: System :: Networking :: Monitoring',
    ]
)
