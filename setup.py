import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(here, 'netdumplings', '_version.py')) as ver_file:
    exec(ver_file.read(), version)

with open('README.rst', 'r') as f:
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
    'scapy-python3==0.23',
    'termcolor',
    'websockets~=4.0.0',
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
            'nd-printer=netdumplings.console:printer_cli',
            'nd-shifty=netdumplings.console:shifty_cli',
            'nd-shiftydetails=netdumplings.console:shiftydetails_cli',
            'nd-shiftysummary=netdumplings.console:shiftysummary_cli',
            'nd-snifty=netdumplings.console:snifty_cli',
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
