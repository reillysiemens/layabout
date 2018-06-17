#!/usr/bin/env python3
import re
import sys
from pathlib import Path

from setuptools import setup

if sys.version_info < (3, 6):
    sys.exit('Only Python 3.6+ is supported.')


def get_version(string: str) -> str:
    """
    Get a version string from a string with a ``__version__`` attribute.

    Args:
        string: The string to search for a version substring.

    Returns:
        The parsed version string.

    Raises:
        RuntimeError: If a version string could not be matched.
    """
    flags = re.S
    pattern = r".*__version__ = '(.*?)'"
    match = re.match(pattern=pattern, string=string, flags=flags)

    if match:
        return match.group(1)

    raise RuntimeError('No version string could be matched')


here = Path(__name__).cwd()
readme = (here / 'README.rst').read_text()
version = get_version((here / 'layabout.py').read_text())

# Requirements.
install_reqs = [
    'slackclient==1.2.1',
]
test_reqs = [
    'flake8',
    'mypy',
    'pytest',
    'pytest-cov',
]
docs_reqs = [
    'Sphinx',
    'sphinx-autodoc-typehints',
]
dev_reqs = test_reqs + docs_reqs

setup(
    name='layabout',
    version=version,
    description='A small event handling library on top of the Slack RTM API. ',
    long_description=readme,
    author='Reilly Tucker Siemens',
    author_email='reilly@tuckersiemens.com',
    url='https://github.com/reillysiemens/wb2k',
    install_requires=install_reqs,
    license='ISCL',
    zip_safe=False,
    py_modules=['layabout'],
    keywords='Slack RTM API',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
    ],
    test_suite='tests',
    tests_require=test_reqs,
    extras_require={
        'dev': dev_reqs,
        'docs': docs_reqs,
        'test': test_reqs,
    },
)
